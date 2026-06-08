from fastapi import FastAPI
from fastapi import UploadFile
from fastapi import File
from fastapi import Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from model.parser import extract_pdf
from model.embedding import calculate_similarity
from model.rule import analyze_resume_structure
from model.llm import analyze_resume , Market_Analysis

from googletrans import Translator

import json
import os
import re
import shutil
import asyncio
import requests
from github import Github
from datetime import datetime, timedelta


NEWS_API_KEY = "977f1f33121447a09fb2afcc603802fb"
g = Github() 
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
        import asyncio
        result = await asyncio.wait_for(
            asyncio.to_thread(translator.translate, req.text, req.target_lang),
            timeout=30.0
        )
        return {"translatedText": result.text}
    except asyncio.TimeoutError:
        print(f"Translation timeout for: {req.text[:50]}...")
        return {"translatedText": req.text}
    except Exception as e:
        print(f"Translation error: {e}")
        return {"translatedText": req.text}

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    job_title: str = Form(...),
    job_type: str = Form(""),
    is_new_grad: str = Form("false"),
    language: str = Form("en")
):

    pdf_path = f"{UPLOAD_DIR}/{file.filename}"

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
        "en"
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
                        candidate = re.sub(r",\s*}" , "}", candidate)
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
    
    

def get_hackernews():
    try:
        top_ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=10
        ).json()

        stories = []

        for story_id in top_ids[:10]:
            item = requests.get(
                f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                timeout=20
            ).json()

            stories.append({
                "title": item.get("title"),
                "url": item.get("url"),
                "score": item.get("score")
            })

        return stories

    except Exception as e:
        print("HackerNews Error:", e)
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


def get_newsapi():
    try:
        url = (
            "https://newsapi.org/v2/everything"
            "?q=technology OR AI OR programming"
            "&language=en"
            "&sortBy=publishedAt"
            f"&apiKey={NEWS_API_KEY}"
        )

        data = requests.get(url, timeout=20).json()

        articles = []

        for article in data.get("articles", [])[:5]:
            articles.append({
                "title": article.get("title"),
                "description": article.get("description")
            })

        return articles

    except Exception as e:
        print("NewsAPI Error:", e)
        return []

def get_newsapi():
    try:
        url = (
            "https://newsapi.org/v2/everything"
            "?q=technology OR AI OR programming"
            "&language=en"
            "&sortBy=publishedAt"
            f"&apiKey={NEWS_API_KEY}"
        )

        data = requests.get(url, timeout=20).json()

        articles = []

        for article in data.get("articles", [])[:5]:
            articles.append({
                "title": article.get("title"),
                "description": article.get("description")
            })

        return articles

    except Exception as e:
        print("NewsAPI Error:", e)
        return []
    

@app.post("/analyze-market")
async def analyze_market():
    hacker_news = get_hackernews()
    github_trending = get_github_trending()
    tech_news = get_newsapi()

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
        return {
            "status": "error",
            "raw_response": llm_response
        }
