from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from model.parser import extract_pdf, PDFExtractError
from model.embedding import calculate_similarity
from model.rule import analyze_resume_structure
from model.jsonutil import parse_llm_json
from model.llm import analyze_resume, Market_Analysis
from model import database as db
from model import job_sources
from model import job_service
from model import matcher
from logger import logger

try:
    from googletrans import Translator
    translator = Translator()
except Exception as e:
    # googletrans is fragile (private API + httpx/httpcore version drift).
    # The /translate endpoint degrades to echo instead of crashing imports.
    translator = None
    logger.warning(f"Translator unavailable, /translate will echo: {e}")
from dotenv import load_dotenv
from github import Github
import json
import os
import re
import shutil
import asyncio
import uuid
import httpx
from datetime import datetime, timedelta

# Load environment variables from .env file (real environment wins over file —
# important for docker-compose `environment:` and for hermetic tests).
load_dotenv(override=False)

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

g = Github()

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        db.init_db()
    except Exception as e:
        logger.error(f"DB init failed: {e}")
    try:
        from model.llm import _provider as _llm_provider
        prov = _llm_provider()
        extra = ""
        if prov in ("google", "gemini"):
            extra = f" model={os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')}"
        logger.info(f"LLM provider={prov}{extra}")
    except Exception:
        pass
    # Server pulls postings by itself: seed when empty + periodic refresh.
    seed_task = None
    scheduler_on = os.getenv("JOBS_AUTO_REFRESH", "1") == "1"
    try:
        if os.getenv("JOBS_AUTO_SEED", "1") == "1" and db.count_jobs() == 0:
            seed_task = asyncio.create_task(job_service.startup_seed())
        if scheduler_on:
            job_service.start_scheduler()
    except Exception as e:
        logger.warning(f"Jobs service start failed: {e}")
    yield
    try:
        if seed_task is not None and not seed_task.done():
            seed_task.cancel()
        await job_service.stop_scheduler()
    except Exception:
        pass


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize translator (may be None if googletrans failed to import — see above)

# Request model for translation
class TranslateRequest(BaseModel):
    text: str
    target_lang: str = "th"

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_UPLOAD_MB = float(os.getenv("MAX_UPLOAD_MB", "10"))
MAX_UPLOAD_BYTES = int(MAX_UPLOAD_MB * 1024 * 1024)
MAX_JOB_TITLE_LEN = 200
MAX_JOB_TYPE_LEN = 100


def _safe_upload_filename(original):
    base = os.path.basename(original or "resume.pdf")
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    if not base:
        base = "resume.pdf"
    stem, ext = os.path.splitext(base)
    stem = (stem or "resume")[:50]
    return f"{uuid.uuid4().hex}_{stem}{ext or '.pdf'}"


def _save_upload_with_limit(upload_file, dest_path, limit_bytes):
    """Stream an upload to disk, aborting above limit_bytes. Returns size."""
    total = 0
    try:
        with open(dest_path, "wb") as out:
            while True:
                chunk = upload_file.file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > limit_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large (limit {MAX_UPLOAD_MB:g} MB)",
                    )
                out.write(chunk)
    except HTTPException:
        try:
            os.remove(dest_path)
        except OSError:
            pass
        raise
    return total


def _current_user_id(authorization=None):
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(None, 1)[1].strip()
    if not token:
        return None
    try:
        user = db.get_user_by_token(token)
    except Exception:
        return None
    return user["id"] if user else None


# googletrans destination codes per UI language.
TRANSLATE_DEST = {"zh": "zh-cn"}


@app.post("/translate")
async def translate_text(req: TranslateRequest):
    """Translate text to target language using googletrans"""
    try:
        if not req.text or req.text.strip() == "":
            return {"translatedText": req.text}

        if translator is None:
            logger.warning("Translator unavailable, echoing original text")
            return {"translatedText": req.text}

        dest = TRANSLATE_DEST.get((req.target_lang or "th").strip().lower(),
                                  (req.target_lang or "th").strip().lower() or "th")
        # googletrans can be slow sometimes, adding delay tolerance
        result = await asyncio.wait_for(
            asyncio.to_thread(translator.translate, req.text, dest),
            timeout=30.0
        )
        return {"translatedText": result.text}
    except asyncio.TimeoutError:
        logger.warning(f"Translation timeout for: {req.text[:50]}...")
        return {"translatedText": req.text}
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return {"translatedText": req.text}

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    job_title: str = Form(...),
    job_type: str = Form(""),
    is_new_grad: str = Form("false"),
    language: str = Form("en"),
    authorization: str = Header(default=None),
):
    job_title = (job_title or "").strip()
    if not job_title:
        raise HTTPException(status_code=400, detail="job_title is required")
    if len(job_title) > MAX_JOB_TITLE_LEN:
        raise HTTPException(
            status_code=400,
            detail=f"job_title too long (max {MAX_JOB_TITLE_LEN} chars)",
        )
    job_type = (job_type or "").strip()[:MAX_JOB_TYPE_LEN]

    if file is None or not file.filename:
        raise HTTPException(status_code=400, detail="resume PDF file is required")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Only PDF files are accepted")
    content_type = (file.content_type or "").lower()
    if content_type and "pdf" not in content_type and "octet-stream" not in content_type:
        raise HTTPException(status_code=415, detail="Only PDF files are accepted")

    logger.info(f"Analyzing resume: {file.filename} for job: {job_title}")

    # Unique filename per request: no collisions, no overwrites.
    pdf_path = os.path.join(UPLOAD_DIR, _safe_upload_filename(file.filename))

    try:
        _save_upload_with_limit(file, pdf_path, MAX_UPLOAD_BYTES)

        try:
            resume_text = extract_pdf(pdf_path)
        except PDFExtractError as e:
            raise HTTPException(status_code=422, detail=str(e))

        try:
            similarity = calculate_similarity(resume_text, job_title)
        except Exception as e:
            logger.error(f"Similarity failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to compute job match")

        rules = analyze_resume_structure(resume_text)

        normalized_language = language.strip().lower()
        if normalized_language not in ("en", "th"):
            normalized_language = "en"

        try:
            llm_result = analyze_resume(
                resume_text,
                job_title,
                similarity,
                rules,
                job_type,
                is_new_grad.lower() in ("true", "1", "yes"),
                normalized_language
            )
        except RuntimeError as e:
            # Provider-level failure (e.g. Gemini overloaded / bad model name).
            # 502, not 500: our code is fine, the upstream AI service failed.
            logger.error(f"LLM provider failed: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"AI provider unavailable "
                       f"({os.getenv('LLM_PROVIDER', 'local')}): {e}")
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            raise HTTPException(status_code=500, detail="AI analysis failed")

        def parse_json(text):
            return parse_llm_json(text)

        parsed = parse_json(llm_result)
        parse_ok = parsed is not None
        if not parse_ok:
            head = (llm_result or "")[:300].replace("\n", " ")
            logger.warning(
                f"LLM output unparseable (len={len(llm_result or '')}): {head}...")

        # AI job picks: top-3 real postings matching this resume (best effort).
        # Pre-filtered by the requested title/type + resume keywords, so the
        # embedding model only ever scores a capped handful — never bulk jobs.
        try:
            suggested_jobs = matcher.suggest_jobs(
                resume_text, limit=3, job_title=job_title, job_type=job_type)
        except Exception as e:
            logger.warning(f"Job suggestion failed: {e}")
            suggested_jobs = []

        # Ensure job_match is a rounded number
        try:
            job_match_val = round(float(similarity), 2)
        except Exception:
            job_match_val = similarity

        try:
            resume_score = None
            if isinstance(parsed, dict) and parsed.get("resume_score") is not None:
                resume_score = float(parsed["resume_score"])
        except (TypeError, ValueError):
            resume_score = None

        # Best-effort history (only when a valid Bearer token is provided).
        history_id = None
        try:
            user_id = _current_user_id(authorization)
            history_id = db.save_analysis(
                user_id=user_id,
                job_title=job_title,
                job_type=job_type,
                job_match=job_match_val if isinstance(job_match_val, (int, float)) else None,
                resume_score=resume_score,
                language=normalized_language,
            )
            db.write_log("analyze", f"{job_title} match={job_match_val}", user_id=user_id)
        except Exception as e:
            logger.warning(f"History save failed: {e}")

        return {
            "job_match": job_match_val,
            "job_title": job_title,
            "is_new_grad": str(is_new_grad),
            "language": normalized_language,
            "rules": rules,
            "analysis_raw": llm_result,
            "analysis": parsed if parsed is not None else llm_result,
            "analysis_parse_ok": parse_ok,
            "history_id": history_id,
            "suggested_jobs": suggested_jobs,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        raise HTTPException(status_code=500, detail="Analysis failed")
    finally:
        # Always clean up the temp upload — no leftover files.
        try:
            if os.path.isfile(pdf_path):
                os.remove(pdf_path)
        except OSError as e:
            logger.warning(f"Upload cleanup failed for {pdf_path}: {e}")

async def get_hackernews():
    try:
        async with httpx.AsyncClient() as client:
            top_ids_resp = await client.get(
                "https://hacker-news.firebaseio.com/v0/topstories.json",
                timeout=10
            )
            top_ids = top_ids_resp.json()

            stories = []
            # Fetch first 10 stories in parallel
            tasks = [client.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json", timeout=10) for story_id in top_ids[:10]]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for res in results:
                if isinstance(res, httpx.Response):
                    item = res.json()
                    stories.append({
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "score": item.get("score")
                    })
            return stories
    except Exception as e:
        logger.error(f"HackerNews Error: {e}")
        return []

def get_github_trending():
    since = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    query = f"created:>{since}"

    repos = g.search_repositories(
        query=query,
        sort="stars",
        order="desc"
    )

    result = []

    for repo in repos[:20]:
        result.append({
            "name": repo.full_name,
            "description": repo.description,
            "stars": repo.stargazers_count,
            "language": repo.language,
            "url": repo.html_url
        })

    return result

async def get_newsapi():
    if not NEWS_API_KEY:
        logger.error("NewsAPI key missing in environment")
        return []
        
    try:
        url = (
            "https://newsapi.org/v2/everything"
            "?q=technology OR AI OR programming"
            "&language=en"
            "&sortBy=publishedAt"
            f"&apiKey={NEWS_API_KEY}"
        )

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=20)
            data = resp.json()

            articles = []
            for article in data.get("articles", [])[:5]:
                articles.append({
                    "title": article.get("title"),
                    "description": article.get("description")
                })
            return articles
    except Exception as e:
        logger.error(f"NewsAPI Error: {e}")
        return []

@app.post("/analyze-market")
async def analyze_market():
    logger.info("Starting market analysis")
    # Fetch all data sources in parallel
    hacker_news_task = get_hackernews()
    github_trending_task = asyncio.to_thread(get_github_trending)
    tech_news_task = get_newsapi()

    hacker_news, github_trending, tech_news = await asyncio.gather(
        hacker_news_task,
        github_trending_task,
        tech_news_task
    )

    combined_data = {
        "hacker_news": hacker_news,
        "github_trending": github_trending,
        "news_api": tech_news
    }
    
    llm_response = Market_Analysis(
        json.dumps(combined_data, ensure_ascii=False)
    )
    
    try:
        parsed_json = json.loads(llm_response)
        return {
            "status": "success",
            "top_emerging_technologies": parsed_json.get("top_emerging_technologies", []),
            "popular_tools": parsed_json.get("popular_tools", []),
            "ai_engineer_relevant": parsed_json.get("ai_engineer_relevant", []),
            "student_relevant": parsed_json.get("student_relevant", []),
            "recommended_skills": parsed_json.get("recommended_skills", []),
            "market_summary": parsed_json.get("market_summary", "")
        }
    except json.JSONDecodeError:
        logger.error(f"Failed to parse LLM response for market analysis: {llm_response}")
        return {
            "status": "error",
            "raw_response": llm_response
        }

# ---------------- jobs (real postings cached in DB) ----------------

@app.get("/jobs")
async def api_list_jobs(q: str = "", location: str = "", source: str = "",
                        job_type: str = "", limit: int = 50, offset: int = 0):
    try:
        return db.list_jobs(q=q, location=location, source=source,
                            job_type=job_type, limit=limit, offset=offset)
    except Exception:
        logger.exception("List jobs failed")
        raise HTTPException(status_code=500, detail="Failed to list jobs")


@app.get("/jobs/status")
async def api_jobs_status():
    return job_service.get_status()


@app.get("/jobs/{job_id}")
async def api_get_job(job_id: int):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


class RefreshRequest(BaseModel):
    limit_per_source: int = 30


@app.post("/jobs/refresh")
async def api_refresh_jobs(req: RefreshRequest):
    limit = max(1, min(req.limit_per_source, 100))
    logger.info("Jobs refresh triggered via API")
    try:
        return await job_service.refresh_now(limit_per_source=limit)
    except Exception as e:
        logger.error(f"Jobs refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Jobs refresh failed")


# ---------------- auth + history + saved jobs ----------------

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def _bearer_token(authorization: str = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return authorization.split(None, 1)[1].strip()


@app.post("/auth/register")
async def api_register(req: RegisterRequest):
    try:
        user = db.create_user(req.name, req.email, req.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    token = db.create_session(user["id"])
    db.write_log("register", req.email, user_id=user["id"])
    logger.info(f"User registered: {req.email}")
    return {"token": token, "user": user}


@app.post("/auth/login")
async def api_login(req: LoginRequest):
    user = db.verify_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = db.create_session(user["id"])
    db.write_log("login", req.email, user_id=user["id"])
    logger.info(f"User login: {req.email}")
    return {"token": token, "user": user}


@app.post("/auth/logout")
async def api_logout(authorization: str = Header(default=None)):
    try:
        token = _bearer_token(authorization)
        db.delete_session(token)
    except HTTPException:
        raise
    except Exception:
        pass
    return {"status": "success"}


@app.get("/me")
async def api_me(authorization: str = Header(default=None)):
    token = _bearer_token(authorization)
    user = db.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


@app.get("/history")
async def api_history(authorization: str = Header(default=None),
                      limit: int = 50, offset: int = 0):
    token = _bearer_token(authorization)
    user = db.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"history": db.list_history(user["id"], limit=limit, offset=offset)}


@app.post("/jobs/{job_id}/save")
async def api_save_job(job_id: int, authorization: str = Header(default=None)):
    token = _bearer_token(authorization)
    user = db.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        db.save_job_for_user(user["id"], job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"status": "success"}


@app.get("/saved-jobs")
async def api_saved_jobs(authorization: str = Header(default=None)):
    token = _bearer_token(authorization)
    user = db.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"jobs": db.list_saved_jobs(user["id"])}


# ---------------- admin / service dashboard (read-only, no secrets) ----------------

@app.get("/admin/stats")
async def api_admin_stats():
    out = {"errors": {}}
    try:
        import time as _time
        path = db.db_path()
        try:
            size = os.path.getsize(path)
        except OSError:
            size = -1
        conn = db._connect()
        try:
            per_source = {
                r["source"]: r["c"]
                for r in conn.execute(
                    "SELECT source, COUNT(*) c FROM jobs GROUP BY source")
            }
            counts = {}
            for table in ("jobs", "users", "sessions", "analysis_history",
                          "saved_jobs", "app_logs"):
                counts[table] = conn.execute(
                    f"SELECT COUNT(*) c FROM {table}").fetchone()["c"]
        finally:
            conn.close()
        out["db"] = {"path": path, "size_bytes": size,
                     "tables": counts, "per_source": per_source}
    except Exception as e:
        logger.exception("admin stats db failed")
        out["errors"]["db"] = f"{type(e).__name__}: {e}"
    try:
        out["jobs_service"] = job_service.get_status()
    except Exception as e:
        out["errors"]["jobs_service"] = f"{type(e).__name__}: {e}"
    out["config"] = {
        "auto_seed": os.getenv("JOBS_AUTO_SEED", "1") == "1",
        "auto_refresh": os.getenv("JOBS_AUTO_REFRESH", "1") == "1",
        "interval_hours": os.getenv("JOBS_REFRESH_HOURS", "6"),
        "max_upload_mb": os.getenv("MAX_UPLOAD_MB", "10"),
        "db_path": db.db_path(),
        "diverse_fetch": os.getenv("JOBS_DIVERSE", "1") == "1",
        "llm_provider": os.getenv("LLM_PROVIDER", "local"),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        "google_key_set": bool(os.getenv("GOOGLE_API_KEY", "").strip()),
    }
    try:
        from model import google_llm as _g
        out["config"]["gemini_model_used"] = _g.last_model
    except Exception:
        pass
    return out


@app.get("/admin/logs")
async def api_admin_logs(limit: int = 50):
    limit = max(1, min(limit, 200))
    conn = db._connect()
    try:
        rows = conn.execute(
            "SELECT * FROM app_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return {"logs": [dict(r) for r in rows]}
    finally:
        conn.close()


@app.get("/admin/source-check")
async def api_admin_source_check():
    """Ping every job source live (read-only, nothing stored)."""
    import time as _time

    async def check(name, fn):
        t0 = _time.time()
        try:
            async with httpx.AsyncClient(
                    headers={"User-Agent": "AI-Resume-App/1.0"}) as client:
                jobs = await asyncio.wait_for(fn(client, 3), timeout=25)
            ms = int((_time.time() - t0) * 1000)
            sample = (jobs[0]["title"] if jobs else "")
            return {"ok": True, "ms": ms, "sample": len(jobs), "example": sample}
        except Exception as e:
            return {"ok": False, "ms": int((_time.time() - t0) * 1000),
                    "sample": 0, "error": f"{type(e).__name__}: {str(e)[:150]}"}

    gated = {
        "adzuna": bool(os.getenv("ADZUNA_APP_ID") and os.getenv("ADZUNA_APP_KEY")),
        "google_jobs": bool(os.getenv("SERPAPI_KEY")),
    }
    results = {}
    for name, fn in job_sources.FETCHERS.items():
        if name in gated and not gated[name]:
            results[name] = {"ok": True, "configured": False, "sample": 0,
                             "note": "needs API key (see README)"}
        elif name in ("linkedin", "facebook"):
            results[name] = {"ok": True, "configured": False, "sample": 0,
                             "note": "no public API — adapter slot reserved"}
        else:
            results[name] = await check(name, fn)
    return {"sources": results}


def runnodejs():
    import subprocess
    import time
    try:
        root = os.path.dirname(os.path.abspath(__file__))
        script = os.path.join(root, "web", "server.js")
        env = dict(os.environ)
        # Keep Node -> backend on 127.0.0.1 (see server.js note about localhost).
        env.setdefault("BACKEND_URL",
                       f"http://127.0.0.1:{os.getenv('PORT', '8000')}")
        process = subprocess.Popen(
            ["node", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=root,
            env=env,
        )
        time.sleep(2)
        if process.poll() is not None:
            # Died immediately (e.g. port in use, missing modules) — surface why.
            try:
                _, err = process.communicate(timeout=5)
            except Exception:
                err = ""
            logger.error(f"Node.js exited early (code {process.returncode}): {(err or '')[-2000:]}")
            return None
        logger.info(f"Node.js server started (PID: {process.pid})")
        return process
    except Exception as e:
        logger.error(f"Node.js script error: {e}")
        return None

if __name__ == "__main__":
    import uvicorn

    node_process = None
    try:
        node_process = runnodejs()
        if node_process is None:
            logger.warning("Node.js server failed to start, continuing with FastAPI only")
    except Exception as e:
        logger.error(f"Failed to start Node.js server: {e}")

    try:
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 8000))
        uvicorn.run(app, host=host, port=port)
    except Exception as e:
        logger.error(f"Failed to start FastAPI server: {e}")
        print(f"Error: {e}")
    finally:
        if node_process and node_process.poll() is None:
            logger.info("Shutting down Node.js server...")
            node_process.terminate()
