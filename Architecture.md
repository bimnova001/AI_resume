Resume PDF
    │
    ▼
PDF Parser
    │
    ▼
Resume Text
    │
    ├──► BGE-M3
    │        │
    │        ▼
    │   Similarity Score
    │
    └──► Qwen2.5-7B
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
 BGE-M3       Qwen2.5-7B
 Matching      Analysis
    │                │
    └───────┬────────┘
            ▼
        JSON Result
            ▼
      Frontend UI