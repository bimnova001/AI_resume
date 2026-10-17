import re

_PATTERNS = {
    # Section headers with word boundaries (EN + common TH headings).
    "education": [
        r"\beducation\b", r"\bacademic\b", r"\bdegree\b", r"\buniversity\b",
        r"\bcollege\b", r"\bgpa\b", r"การศึกษา", r"วุฒิการศึกษา", r"ปริญญา",
    ],
    "skills": [
        r"\bskills?\b", r"\btech stack\b", r"\btechnologies\b", r"\btools\b",
        r"ทักษะ", r"ความสามารถ",
    ],
    "projects": [
        r"\bprojects?\b", r"\bportfolio project\b", r"\bpersonal project\b",
        r"โครงการ", r"ผลงาน",
    ],
    "experience": [
        r"\bexperience\b", r"\bemployment\b", r"\bwork history\b",
        r"\bintern(ship)?\b", r"ประสบการณ์", r"ประสบการณ์ทำงาน", r"ฝึกงาน",
    ],
    "github": [
        r"github\.com/[\w.-]+",
    ],
    "portfolio": [
        r"\bportfolio\b", r"\bpersonal website\b", r"\bbehance\b",
        r"\bdribbble\b", r"พอร์ตโฟลิโอ",
    ],
    "contact_email": [r"[\w.+-]+@[\w-]+\.[\w.]+"],
    "contact_phone": [r"\+?\d[\d\s\-()]{7,}\d"],
    "linkedin": [r"linkedin\.com/\S+"],
}

# Contact patterns are informational only (not required sections).


def analyze_resume_structure(text):
    result = {
        "education": False,
        "skills": False,
        "projects": False,
        "experience": False,
        "github": False,
        "portfolio": False,
    }

    if not isinstance(text, str) or not text.strip():
        result["details"] = {"error": "empty text"}
        return result

    lower_text = text.lower()
    details = {}
    for key, patterns in _PATTERNS.items():
        matches = []
        for pat in patterns:
            try:
                m = re.search(pat, lower_text, re.IGNORECASE)
            except re.error:
                continue
            if m:
                matches.append(m.group(0)[:80])
                break
        details[key] = matches[0] if matches else None
        if key in result:
            result[key] = bool(matches)

    result["details"] = details
    return result
