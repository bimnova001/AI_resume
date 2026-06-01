from fastapi import FastAPI
from fastapi import UploadFile
from fastapi import File
from fastapi import Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from model.parser import extract_pdf
from model.embedding import calculate_similarity
from model.rule import analyze_resume_structure
from model.llm import analyze_resume

from googletrans import Translator

import json
import os
import re
import shutil
import asyncio

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