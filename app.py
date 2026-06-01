from fastapi import FastAPI
from fastapi import UploadFile
from fastapi import File
from fastapi import Form
from fastapi.middleware.cors import CORSMiddleware

from model.parser import extract_pdf
from model.embedding import calculate_similarity
from model.rule import analyze_resume_structure
from model.llm import analyze_resume

import json
import os
import re
import shutil

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

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

    llm_result = analyze_resume(
        resume_text,
        job_title,
        similarity,
        rules,
        job_type,
        is_new_grad.lower() in ("true", "1", "yes"),
        language
    )
    

    def parse_json(text):
        if not isinstance(text, str):
            return None
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    return None
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
        "rules": rules,
        "analysis_raw": llm_result,
        "analysis": parsed if parsed is not None else llm_result
    }