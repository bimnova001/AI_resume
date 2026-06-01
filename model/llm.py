import json
from llama_cpp import Llama

llm = Llama.from_pretrained(
	repo_id="Qwen/Qwen2.5-3B-Instruct-GGUF",
	filename="qwen2.5-3b-instruct-q4_k_m.gguf",
    n_ctx=2048,
    n_threads=4,
    verbose=False,
    cache_dir="./model_cache"
    
)
def analyze_resume(
    resume_text,
    job_title,
    similarity,
    rules,
    job_type="",
    is_new_grad=False,
    language="en"
):

    requested_language = "English"
    prompt = f"""
You are a professional HR expert.

Job Position:
{job_title}

Job Type:
{job_type}

New Graduate:
{"Yes" if is_new_grad else "No"}

Resume:
{resume_text[:4000]}

Resume Rule Analysis:
{rules}

Job Match Score:
{similarity}

Instructions:
- Answer in English.
- Keep the JSON keys in English exactly as shown below.
- Return ONLY valid JSON. Do not include any extra text outside the JSON object.
- you should analyze the resume based on the job title, job type, new graduate status, and the provided rules.
- Provide a comprehensive analysis of the resume's suitability for the job, including strengths, weaknesses, missing skills, and recommendations for improvement.
- The analysis should be based on the content of the resume and how well it matches the job requirements, as well as the structure of the resume as indicated by the rules.
- The job match score should be used to inform the analysis, but the final resume score should be a holistic assessment of the candidate's fit for the job, not just a reflection of the match score.

Format:

{{
  "resume_score": 0,
  "match_comment": "",
  "summary": "",
  "strengths": [],
  "weaknesses": [],
  "missing_skills": [],
  "recommended_projects": [],
  "recommended_certificates": [],
  "career_paths": [],
  "recommended_actions": []
}}
"""

    result = llm.create_completion(
        prompt=prompt,
        max_tokens=700,
        temperature=0.0
    )

    return result["choices"][0]["text"]