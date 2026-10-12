"""Match a resume against real postings in the DB (stdlib only).

Pipeline (fast, no extra LLM call):
  1. extract_keywords() — frequent meaningful tokens from the resume,
  2. candidate pre-filter via SQLite LIKE search per keyword (cheap),
  3. embedding cosine re-rank of a capped candidate set (accurate),
  4. matched_skills — keyword overlap shown as the human-readable reason.

Returns up to `limit` jobs shaped for the API:
  {id, title, company, location, type, salary, url, source, posted_at,
   match (0-100), matched_skills [...], reason}
"""
import re
from collections import Counter

_STOPWORDS = frozenset("""
a an the and or of to in on for with as at by from is are was were be been being
it its this that these those you your we our they their he she his her him them
will would can could should may might must shall do does did done have has had
not no yes if then than so such very more most own same over under between into
through during about across per via using use used including include within without
work worked working experience experienced skilled skills ability able strong
team player fast learner detail oriented motivated passionate responsible role
including join joining looking seek seeking candidate successful join team years
year new senior junior etc eg ie profiling profile summary objective highlights
key core proven track record drive driven deliver delivering build built building
develop developed developer development design designed knowledge proficient
familiar tools tool technologies technology various multiple diverse including
thai และ หรือ ของ ใน ที่ เป็น ให้ ได้ กับ จาก มี จะ ไม่ นี้ นั้น ที่สุด สำหรับ
ประสบการณ์ ทักษะ ความสามารถ ทำงาน บริษัท ศึกษา ระดับ ปริญญา
""".split())


def tokenize(text):
    if not isinstance(text, str):
        return []
    return re.findall(r"[A-Za-z][A-Za-z0-9+#.\-]{1,30}", text.lower())


def extract_keywords(text, top_n=12):
    """Most frequent non-stopword tokens — the resume's skill vocabulary."""
    counts = Counter(t for t in tokenize(text) if t not in _STOPWORDS)
    # Prefer tech-looking tokens (with + # . or digits) on ties.
    ranked = sorted(counts.items(),
                    key=lambda kv: (kv[1], bool(re.search(r"[+#.\d]", kv[0]))),
                    reverse=True)
    return [w for w, _ in ranked[:max(1, top_n)]]


def job_search_text(job):
    return " ".join(str(job.get(k, "")) for k in
                    ("title", "company", "description", "tags") if job.get(k))


def matched_skills(resume_keywords, job, max_n=6):
    job_tokens = set(tokenize(job_search_text(job)))
    if isinstance(job.get("tags"), list):
        job_tokens.update(t.lower() for t in job["tags"] if isinstance(t, str))
    return [kw for kw in resume_keywords if kw in job_tokens][:max_n]


def suggest_jobs(resume_text, limit=3, candidate_cap=15, similarity_fn=None):
    """Top-`limit` DB postings for this resume. Never raises.

    `similarity_fn(resume, job_text)` injected for tests; defaults to the
    embedding model (imported lazily to keep this module light).
    """
    from model import database as db

    if similarity_fn is None:
        from model.embedding import calculate_similarity as similarity_fn

    if not isinstance(resume_text, str) or not resume_text.strip():
        return []
    try:
        keywords = extract_keywords(resume_text)
        if not keywords:
            return []

        # 1) cheap pre-filter: union of per-keyword searches
        seen, candidates = set(), []
        for kw in keywords[:8]:
            try:
                out = db.list_jobs(q=kw, limit=candidate_cap, offset=0)
            except Exception:
                continue
            for job in out.get("jobs", []):
                if job.get("id") not in seen and job.get("title"):
                    seen.add(job["id"])
                    candidates.append(job)
                if len(candidates) >= candidate_cap:
                    break
            if len(candidates) >= candidate_cap:
                break
        if not candidates:
            return []

        # 2) accurate re-rank with embeddings
        scored = []
        for job in candidates:
            try:
                text = f"{job.get('title', '')}. {(job.get('description') or '')[:1500]}"
                score = float(similarity_fn(resume_text[:8000], text))
            except Exception:
                continue
            skills = matched_skills(keywords, job)
            scored.append((score, skills, job))
        scored.sort(key=lambda t: t[0], reverse=True)

        # 3) shape results with human-readable reasons
        results = []
        for score, skills, job in scored[:max(1, limit)]:
            skill_txt = ", ".join(skills) if skills else "overall profile fit"
            results.append({
                "id": job.get("id"),
                "title": job.get("title"),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "type": job.get("type", ""),
                "salary": job.get("salary", ""),
                "url": job.get("url", ""),
                "source": job.get("source", ""),
                "posted_at": job.get("posted_at", ""),
                "match": round(score, 2),
                "matched_skills": skills,
                "reason": f"Match {score:.1f}% — overlaps your resume on: {skill_txt}.",
            })
        return results
    except Exception:
        return []
