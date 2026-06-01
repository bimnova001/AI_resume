import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Allow using a lightweight embedding model via env var USE_SMALL_EMBEDDING
use_small = os.getenv("USE_SMALL_EMBEDDING", "false").lower() in ("1", "true", "yes")
device = os.getenv("EMBEDDING_DEVICE", "cpu")

if use_small:
    model_name = "all-MiniLM-L6-v2"
else:
    model_name = "BAAI/bge-m3"

model = SentenceTransformer(model_name, device=device, cache_folder="./model_cache")

def calculate_similarity(resume_text, job_text):
    resume_emb = model.encode(resume_text)
    job_emb = model.encode(job_text)

    score = cosine_similarity([resume_emb], [job_emb])[0][0]

    return round(float(score * 100), 2)