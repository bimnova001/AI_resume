Resume PDF
    │
    ▼
PDF Parser
    │
    ▼
Resume Text
    │
    ├──► BGE-M3 (or all-MiniLM-L6-v2 when USE_SMALL_EMBEDDING=1)
    │        │
    │        ▼
    │   Similarity Score (job-title expanded + normalized cosine)
    │
    └──► Qwen2.5-7B-Instruct-GGUF Q4_K_M (lazy-loaded, JSON mode, LLM_REPO/LLM_FILE/LLM_CTX/LLM_THREADS)
             │
             ▼
       AI Analysis
             │
             ▼
        Final Report



Frontend (Node.js + Express/Next.js)
            │
            ▼
       FastAPI
            │
    ┌───────┴────────┐
    ▼                ▼
 BGE-M3       Qwen2.5-7B-Instruct
 Matching      Analysis
    │                │
    └───────┬────────┘
            ▼
        JSON Result
            ▼
      Frontend UI