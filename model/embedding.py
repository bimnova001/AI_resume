import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Lazy-load embedding model so importing this module is cheap.
# Configure via env: EMBEDDING_MODEL, USE_SMALL_EMBEDDING, EMBEDDING_DEVICE
_model = None

MAX_EMBED_CHARS = 8000


def _resolve_model_name():
    explicit = os.getenv("EMBEDDING_MODEL", "").strip()
    if explicit:
        return explicit
    use_small = os.getenv("USE_SMALL_EMBEDDING", "false").lower() in ("1", "true", "yes")
    if use_small:
        return "all-MiniLM-L6-v2"
    return "BAAI/bge-m3"


def get_model():
    global _model
    if _model is not None:
        return _model
    device = os.getenv("EMBEDDING_DEVICE", "cpu")
    _model = SentenceTransformer(
        _resolve_model_name(), device=device, cache_folder="./model_cache"
    )
    return _model


def _truncate(text, limit=MAX_EMBED_CHARS):
    if not isinstance(text, str):
        return ""
    text = text.strip()
    if len(text) > limit:
        return text[:limit]
    return text


def _expand_job_text(job_text):
    """Short job titles (e.g. 'AI Engineer') give meaningless similarity.

    Expand short inputs into a richer description so cosine similarity
    reflects skills/responsibilities instead of 2-3 words.
    """
    job_text = (job_text or "").strip()
    if len(job_text) >= 200:
        return _truncate(job_text)
    if not job_text:
        return ""
    return (
        f"Job title: {job_text}. "
        f"Required skills, responsibilities, qualifications, tools and "
        f"technologies for a {job_text} role. "
        f"Candidate experience relevant to {job_text}."
    )


def calculate_similarity(resume_text, job_text):
    model = get_model()
    resume_clean = _truncate(resume_text)
    job_clean = _truncate(_expand_job_text(job_text))
    if not resume_clean or not job_clean:
        return 0.0

    resume_emb = model.encode(resume_clean, normalize_embeddings=True)
    job_emb = model.encode(job_clean, normalize_embeddings=True)

    score = cosine_similarity([resume_emb], [job_emb])[0][0]

    return round(float(score * 100), 2)
