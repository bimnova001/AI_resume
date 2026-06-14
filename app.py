from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from model.parser import extract_pdf
from model.embedding import calculate_similarity
from model.rule import analyze_resume_structure
from model.llm import analyze_resume, Market_Analysis
from logger import logger

from googletrans import Translator
from dotenv import load_dotenv

import json
import os
import re
import shutil
import asyncio
import httpx
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize translator
translator = Translator()

# Request model for translation
class TranslateRequest(BaseModel):
    text: str
    target_lang: str = "th"

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/translate")
async def translate_text(req: TranslateRequest):
    """Translate text to target language using googletrans"""
    try:
        if not req.text or req.text.strip() == "":
            return {"translatedText": req.text}
        
        # googletrans can be slow sometimes, adding delay tolerance
        result = await asyncio.wait_for(
            asyncio.to_thread(translator.translate, req.text, req.target_lang),
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
    language: str = Form("en")
):
    logger.info(f"Analyzing resume: {file.filename} for job: {job_title}")
    
    # Secure filename and path
    filename = os.path.basename(file.filename)
    pdf_path = os.path.join(UPLOAD_DIR, filename)

    try:
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        resume_text = extract_pdf(pdf_path)

        similarity = calculate_similarity(
            resume_text,
            job_title
        )

        rules = analyze_resume_structure(
            resume_text
        )

        normalized_language = language.strip().lower()
        if normalized_language not in ("en", "th"):
            normalized_language = "en"

        llm_result = analyze_resume(
            resume_text,
            job_title,
            similarity,
            rules,
            job_type,
            is_new_grad.lower() in ("true", "1", "yes"),
            normalized_language
        )

        def parse_json(text):
            if not isinstance(text, str):
                return None
            text = text.strip()
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                # Try to extract the first balanced JSON object from the string
                start = text.find("{")
                if start == -1:
                    return None
                depth = 0
                in_string = False
                escape = False
                for i in range(start, len(text)):
                    ch = text[i]
                    if escape:
                        escape = False
                        continue
                    if ch == "\\":
                        escape = True
                        continue
                    if ch == '"':
                        in_string = not in_string
                        continue
                    if in_string:
                        continue
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            candidate = text[start:i + 1]
                            candidate = re.sub(r",\s*}", "}", candidate)
                            candidate = re.sub(r",\s*]", "]", candidate)
                            try:
                                return json.loads(candidate)
                            except json.JSONDecodeError:
                                return None
                            break
                return None

        parsed = parse_json(llm_result)

        # Ensure job_match is a rounded number
        try:
            job_match_val = round(float(similarity), 2)
        except Exception:
            job_match_val = similarity

        return {
            "job_match": job_match_val,
            "job_title": job_title,
            "is_new_grad": str(is_new_grad),
            "language": normalized_language,
            "rules": rules,
            "analysis_raw": llm_result,
            "analysis": parsed if parsed is not None else llm_result
        }
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        return {"error": str(e)}

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

def _github_trending_sync(g, limit=10):
    since = (
        datetime.now() - timedelta(days=30)
    ).strftime("%Y-%m-%d")
    query = (
        f"created:>{since} "
        "(AI OR LLM OR machine-learning OR "
        "deep-learning OR agent OR python)"
    )
    repos = g.search_repositories(
        query=query,
        sort="stars",
        order="desc"
    )
    results = []
    for repo in repos[:limit]:
        results.append({
            "name": repo.full_name,
            "description": (
                repo.description
                if repo.description
                else ""
            ),
            "stars": repo.stargazers_count,
            "language": repo.language,
            "topics": repo.get_topics(),
            "url": repo.html_url
        })
    return results



async def get_github_trending(g, limit=10):
    try:
        result = await asyncio.to_thread(
            _github_trending_sync,
            g,
            limit
        )
        return result

    except Exception as e:
        logger.error(
            f"GitHub API Error: {e}"
        )
        return []

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
    github_trending_task = get_github_trending()
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

def runnodejs():
    import subprocess
    try:
        result = subprocess.run(["node", "./web/server.js"], capture_output=True, text=True, check=True)
        print("Node.js server output:", result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Node.js script error: {e.stderr}")
        return None

if __name__ == "__main__":
    try :
        print("Starting FastAPI server...")
        print("localhost: http://localhost:3000")
        import uvicorn
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 8000))
        uvicorn.run(app, host=host, port=port)
        try : 
            runnodejs()
            
        except Exception as e:
            logger.error(f"Failed to start Node.js server: {e}")
            print(f"Error starting Node.js server: {e}")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        print(f"Error: {e}")
