"""Job source adapters: fetch real postings, normalize, store in DB.

Working today (free, no API key):
  - Remotive (remote jobs):  https://remotive.com/api/remote-jobs
  - Arbeitnow (job board):   https://www.arbeitnow.com/api/job-board-api

Optional (set env keys to enable):
  - Adzuna (needs ADZUNA_APP_ID + ADZUNA_APP_KEY): https://developer.adzuna.com
  - Google Jobs via SerpApi (needs SERPAPI_KEY):  https://serpapi.com/google-jobs-api

LinkedIn / Facebook:
  There is NO free official postings API for these networks. Options:
  1) LinkedIn official "Jobs Search" via LinkedIn Marketing/Talent APIs
     (requires company partnership + OAuth) — plug in as a new fetcher.
  2) Facebook Jobs was deprecated; listings now live in Groups/Marketplace
     with no public API — same adapter slot reserved below.
  Both are stubbed as fetch_linkedin()/fetch_facebook() returning [] so the
  pipeline keeps working; implement them when you have API access and drop
  the results into normalize() — no other code changes needed.
"""
import asyncio
import html
import os
import re

import httpx

from model import database as db
from logger import logger

TIMEOUT = 20.0


def strip_html(raw):
    """Remove HTML tags/entities from API descriptions (stdlib only)."""
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", " ", str(raw))
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def normalize(source, raw):
    """Map a raw posting to the common job schema."""
    tags = raw.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    return {
        "external_id": str(raw.get("external_id", raw.get("url", ""))),
        "source": source,
        "title": str(raw.get("title", "")),
        "company": str(raw.get("company", "")),
        "location": str(raw.get("location", "")),
        "type": str(raw.get("type", "")),
        "salary": str(raw.get("salary", "")),
        "description": str(raw.get("description", "")),
        "url": str(raw.get("url", "")),
        "tags": list(tags),
        "posted_at": str(raw.get("posted_at", "")),
    }


# ---------------- free sources (no key) ----------------

async def fetch_remotive(client, limit=50):
    try:
        resp = await client.get(
            "https://remotive.com/api/remote-jobs", params={"limit": limit}, timeout=TIMEOUT
        )
        data = resp.json()
        jobs = []
        for j in data.get("jobs", [])[:limit]:
            jobs.append(normalize("remotive", {
                "external_id": j.get("id"),
                "title": j.get("title"),
                "company": j.get("company_name"),
                "location": j.get("candidate_required_location") or "Remote",
                "type": j.get("job_type") or "Full-time",
                "salary": j.get("salary") or "",
                "description": strip_html(j.get("description"))[:2000],
                "url": j.get("url"),
                "tags": [c for c in (j.get("category"),) if c],
                "posted_at": j.get("publication_date") or "",
            }))
        return jobs
    except Exception as e:
        logger.warning(f"Remotive fetch failed: {e}")
        return []


async def fetch_remoteok(client, limit=50):
    """Remote OK remote jobs (free, no key).

    ToS: link back to the Remote OK URL and mention Remote OK as source.
    We store their canonical URL and surface the source label in the UI.
    """
    try:
        resp = await client.get("https://remoteok.com/api", timeout=TIMEOUT)
        items = resp.json()
        jobs = []
        for j in items:
            if not isinstance(j, dict) or "position" not in j:
                continue  # first item is a legal notice, not a job
            salary = ""
            if j.get("salary_min") or j.get("salary_max"):
                salary = f"${j.get('salary_min', '?')} - ${j.get('salary_max', '?')}"
            jobs.append(normalize("remoteok", {
                "external_id": j.get("id") or j.get("slug"),
                "title": j.get("position"),
                "company": j.get("company"),
                "location": j.get("location") or "Remote",
                "type": "Remote",
                "salary": salary,
                "description": strip_html(j.get("description"))[:2000],
                "url": j.get("url"),
                "tags": j.get("tags") or [],
                "posted_at": j.get("date") or "",
            }))
            if len(jobs) >= limit:
                break
        return jobs
    except Exception as e:
        logger.warning(f"RemoteOK fetch failed: {e}")
        return []


async def fetch_jobicy(client, limit=50):
    """Jobicy remote jobs (free, no key)."""
    try:
        resp = await client.get(
            "https://jobicy.com/api/v2/remote-jobs",
            params={"count": min(limit, 50)}, timeout=TIMEOUT,
        )
        jobs = []
        for j in resp.json().get("jobs", [])[:limit]:
            job_type = j.get("jobType")
            if isinstance(job_type, list):
                job_type = ", ".join(job_type)
            jobs.append(normalize("jobicy", {
                "external_id": j.get("id") or j.get("jobSlug"),
                "title": j.get("jobTitle"),
                "company": j.get("companyName"),
                "location": j.get("jobGeo") or "Remote",
                "type": job_type or "",
                "salary": "",
                "description": strip_html(
                    j.get("jobDescription") or j.get("jobExcerpt"))[:2000],
                "url": j.get("url"),
                "tags": j.get("jobIndustry") or [],
                "posted_at": j.get("pubDate") or "",
            }))
        return jobs
    except Exception as e:
        logger.warning(f"Jobicy fetch failed: {e}")
        return []


async def fetch_muse(client, limit=50):
    """The Muse job listings (free, no key). Paginates until limit."""
    try:
        jobs = []
        page = 0
        while len(jobs) < limit and page < 5:
            resp = await client.get(
                "https://www.themuse.com/api/public/jobs",
                params={"page": page}, timeout=TIMEOUT,
            )
            results = resp.json().get("results", [])
            if not results:
                break
            for j in results:
                company = j.get("company") or {}
                locs = [loc.get("name", "") for loc in (j.get("locations") or [])]
                levels = [lv.get("name", "") for lv in (j.get("levels") or [])]
                refs = j.get("refs") or {}
                jobs.append(normalize("muse", {
                    "external_id": j.get("id"),
                    "title": j.get("name"),
                    "company": company.get("name", "") if isinstance(company, dict) else "",
                    "location": ", ".join(l for l in locs if l),
                    "type": ", ".join(l for l in levels if l),
                    "salary": "",
                    "description": strip_html(j.get("contents"))[:2000],
                    "url": refs.get("landing_page", "") if isinstance(refs, dict) else "",
                    "tags": [c.get("name", "") for c in (j.get("categories") or [])
                             if isinstance(c, dict) and c.get("name")],
                    "posted_at": j.get("publication_date") or "",
                }))
                if len(jobs) >= limit:
                    break
            page += 1
        return jobs[:limit]
    except Exception as e:
        logger.warning(f"Muse fetch failed: {e}")
        return []


async def fetch_arbeitnow(client, limit=50):
    try:
        resp = await client.get(
            "https://www.arbeitnow.com/api/job-board-api", timeout=TIMEOUT
        )
        data = resp.json()
        jobs = []
        for j in data.get("data", [])[:limit]:
            jobs.append(normalize("arbeitnow", {
                "external_id": j.get("slug"),
                "title": j.get("title"),
                "company": j.get("company_name"),
                "location": j.get("location") or "",
                "type": j.get("job_types") and ", ".join(j["job_types"]) or "",
                "salary": "",
                "description": strip_html(j.get("description"))[:2000],
                "url": j.get("url"),
                "tags": j.get("tags") or [],
                "posted_at": j.get("created_at") or "",
            }))
        return jobs
    except Exception as e:
        logger.warning(f"Arbeitnow fetch failed: {e}")
        return []


# ---------------- key-gated sources ----------------

async def fetch_adzuna(client, limit=50):
    app_id = os.getenv("ADZUNA_APP_ID", "")
    app_key = os.getenv("ADZUNA_APP_KEY", "")
    country = os.getenv("ADZUNA_COUNTRY", "th")
    if not app_id or not app_key:
        return []
    try:
        resp = await client.get(
            f"https://api.adzuna.com/v1/api/jobs/{country}/search/1",
            params={"app_id": app_id, "app_key": app_key,
                    "results_per_page": min(limit, 50), "content-type": "application/json"},
            timeout=TIMEOUT,
        )
        jobs = []
        for j in resp.json().get("results", [])[:limit]:
            jobs.append(normalize("adzuna", {
                "external_id": j.get("id"),
                "title": j.get("title"),
                "company": (j.get("company") or {}).get("display_name", ""),
                "location": (j.get("location") or {}).get("display_name", ""),
                "type": j.get("contract_type") or "",
                "salary": j.get("salary_min") and f"{j.get('salary_min')}+" or "",
                "description": strip_html(j.get("description"))[:2000],
                "url": j.get("redirect_url"),
                "tags": (j.get("category") or {}).get("label") and [j["category"]["label"]] or [],
                "posted_at": j.get("created") or "",
            }))
        return jobs
    except Exception as e:
        logger.warning(f"Adzuna fetch failed: {e}")
        return []


async def fetch_google_jobs_serpapi(client, limit=50):
    """Real Google Jobs results via SerpApi (needs SERPAPI_KEY + SEARCH_QUERY)."""
    api_key = os.getenv("SERPAPI_KEY", "")
    if not api_key:
        return []
    try:
        resp = await client.get(
            "https://serpapi.com/search",
            params={"engine": "google_jobs", "q": os.getenv("SEARCH_QUERY", "software engineer jobs"),
                    "api_key": api_key, "num": min(limit, 20)},
            timeout=TIMEOUT,
        )
        jobs = []
        for j in resp.json().get("jobs_results", [])[:limit]:
            ext = (j.get("detected_extensions") or {})
            jobs.append(normalize("google_jobs", {
                "external_id": j.get("job_id"),
                "title": j.get("title"),
                "company": j.get("company_name"),
                "location": j.get("location") or "",
                "type": ext.get("schedule_type") or "",
                "salary": ext.get("salary") or "",
                "description": strip_html(j.get("description"))[:2000],
                "url": (j.get("related_links") or [{}])[0].get("link", "") if j.get("related_links") else "",
                "tags": [],
                "posted_at": ext.get("posted_at") or "",
            }))
        return jobs
    except Exception as e:
        logger.warning(f"SerpApi Google Jobs fetch failed: {e}")
        return []


# ---------------- LinkedIn / Facebook (reserved slots) ----------------

async def fetch_linkedin(client, limit=50):  # noqa: ARG001
    """Reserved: plug LinkedIn official API / compliant provider here."""
    logger.info("LinkedIn source not configured (needs official API access); skipping")
    return []


async def fetch_facebook(client, limit=50):  # noqa: ARG001
    """Reserved: Facebook Jobs has no public API; plug a provider here."""
    logger.info("Facebook source not configured (no public Jobs API); skipping")
    return []


FETCHERS = {
    "remotive": fetch_remotive,
    "arbeitnow": fetch_arbeitnow,
    "remoteok": fetch_remoteok,
    "jobicy": fetch_jobicy,
    "muse": fetch_muse,
    "adzuna": fetch_adzuna,
    "google_jobs": fetch_google_jobs_serpapi,
    "linkedin": fetch_linkedin,
    "facebook": fetch_facebook,
}


async def refresh_jobs(limit_per_source=50, only=None):
    """Fetch enabled sources and upsert into DB. Returns {source: count}."""
    selected = {k: v for k, v in FETCHERS.items() if only is None or k in only}
    counts = {}
    async with httpx.AsyncClient(headers={"User-Agent": "AI-Resume-App/1.0"}) as client:
        results = await asyncio.gather(
            *(fn(client, limit_per_source) for fn in selected.values()),
            return_exceptions=True,
        )
    for source, res in zip(selected.keys(), results):
        if isinstance(res, Exception):
            logger.warning(f"Source {source} error: {res}")
            counts[source] = 0
            continue
        saved = 0
        for job in res or []:
            try:
                db.upsert_job(job)
                saved += 1
            except Exception as e:
                logger.warning(f"Upsert failed ({source}): {e}")
        counts[source] = saved
    try:
        db.write_log("jobs_refresh", str(counts))
    except Exception:
        pass
    return counts
