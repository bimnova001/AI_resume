import re

def analyze_resume_structure(text):

    result = {
        "education": False,
        "skills": False,
        "projects": False,
        "experience": False,
        "github": False,
        "portfolio": False
    }

    lower_text = text.lower()

    if "education" in lower_text:
        result["education"] = True

    if "skill" in lower_text:
        result["skills"] = True

    if "project" in lower_text:
        result["projects"] = True

    if "experience" in lower_text:
        result["experience"] = True

    if "github.com" in lower_text:
        result["github"] = True

    if "portfolio" in lower_text:
        result["portfolio"] = True

    return result