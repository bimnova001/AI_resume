# AI Career Navigator

> AI-powered career planning assistant that helps students bridge the gap between their current skills and industry requirements.

## Overview

Many fresh graduates struggle to find their first job because companies increasingly require candidates with practical experience and industry-ready skills.

**Career Copilot AI** helps students understand:

* What skills they currently have
* What skills they are missing
* How well they match their target job
* What projects they should build
* What technologies are trending in the industry

The goal is to help students create a personalized roadmap to gain experience and become job-ready.

---

##  Resume Analysis

Upload your resume and let AI analyze your current profile.

Provides:

* Resume evaluation
* Strength analysis
* Weakness identification
* Skill extraction
* Improvement suggestions

---

##  Job Matching

Compare your resume with your target position.

Example:

```
Target:
AI Engineer

Result:

Job Match:
78%

Matched Skills:
✓ Python
✓ Machine Learning
✓ PyTorch

Missing Skills:
✗ Docker
✗ SQL
✗ Linux
```

---

##  Skill Gap Analysis

Identify missing skills between:

```
Current Skills
        +
Target Job Requirements
        =
Skill Gap
```

The system recommends what skills should be learned first based on industry demand.

---



```
Missing Skill:
LLM Deployment

Recommended Project:

Build RAG Chatbot

Learn:
- LLM
- Vector Database
- API Deployment
- Docker
```

Trending:

↑ AI Agent
↑ RAG
↑ Local LLM
↑ Vector Database

Recommended:
- LangGraph
- Docker
- vLLM
```

---

#  AI Models 

## Embedding Model

**BGE-M3** (default; set `USE_SMALL_EMBEDDING=1` to use `all-MiniLM-L6-v2` for low-RAM dev)

Used for:

* Resume embedding
* Job description matching
* Semantic similarity search (normalized cosine; short job titles are expanded before encoding)

## Language Model

**Qwen2.5-7B-Instruct (Q4_K_M, chat JSON mode + 1 repair retry)**

Used for:

* Career recommendation
* Resume feedback
* Market trend summarization
* Project recommendation

---

# 🛠 Tech Stack

## Backend

* Python
* FastAPI
* PyMuPDF
* Sentence Transformers

## AI

* BGE-M3
* Qwen2.5-7B-Instruct (Q4_K_M)

## Frontend

* HTML
* CSS
* JavaScript

## Data Sources (jobs — 100% real postings, no mock data)

Free, no key (all verified live, ~130+ postings per refresh):

* Remotive, Arbeitnow, Remote OK, Jobicy, The Muse — `POST /jobs/refresh`
* Optional keys: Adzuna (`ADZUNA_APP_ID`/`ADZUNA_APP_KEY`), Google Jobs via SerpApi (`SERPAPI_KEY`)
* LinkedIn / Facebook: reserved adapter slots in `model/job_sources.py`
  (no free public API — plug official API access when available)
* Every posting stored in SQLite (`DB_PATH`, default `./data/app.db`) with
  title, company, location, type, salary, description, **original URL + posted date + fetched date**
* Server-side search: `GET /jobs?q=&location=&source=&job_type=&limit=&offset=`
* **Server pulls by itself** — users never fetch manually:
  `model/job_service.py` seeds on first boot when empty + re-fetches every
  `JOBS_REFRESH_HOURS` (default 6); `GET /jobs/status` shows total,
  last fetch time, per-source counts and whether a fetch is running;
  `JOBS_AUTO_SEED=0` / `JOBS_AUTO_REFRESH=0` to disable

## Service Dashboard (`/pages/admin.html`)

* DB stats (file size, rows per table, jobs per source), fetch status,
  latest 10 postings with link + posted date, recent service logs
* Buttons: refresh now, live per-source check (read-only, nothing stored)
* Read-only APIs: `GET /admin/stats`, `GET /admin/logs`, `GET /admin/source-check`
* Open the site via **http://localhost:3000** (Node proxy); if a page is served
  from elsewhere, `/js/api.js` talks to the backend directly (`?api=host:port` to override)

## Auth / History (new)

* `POST /auth/register`, `POST /auth/login` → Bearer token
* `GET /me`, `GET /history`, `POST /jobs/{id}/save`, `GET /saved-jobs`
* `/analyze` accepts `Authorization: Bearer <token>`, records history and
  returns **`suggested_jobs`: top-3 real postings ranked by embedding
  similarity to the resume** (`model/matcher.py`), each with match %,
  matched skills, reason, original URL and posted date
* Events also land in `app_logs` table + file logs

## Tests

```
pytest tests/ test.py -v     # 64 tests, no GPU/model download needed
```

## Docker

Prerequisites: Docker Desktop **running**, ~8 GB RAM, ~20 GB free disk
(API image is big: PyTorch + compiled llama + ~4 GB models on first run).

```
cp .env.example .env   # Windows: copy .env.example .env (optional, works without keys)
docker compose up --build
```

* Frontend → http://localhost:3000 · API → http://localhost:8000/docs
* First API start downloads ~7 GB of models into the `model-cache` volume
  (slow once, then cached). DB persists in `./data/`.
* Low-RAM dev: set `USE_SMALL_EMBEDDING=1` on the `api` service.
* Without docker: `pip install -r requirements.txt && python app.py`
  (spawns the Node frontend automatically).

| อยากทำอะไร | คำสั่ง |
|---|---|
| รันทั้งระบบ (แนะนำ) | `docker compose up --build` |
| รันเบื้องหลัง | `docker compose up --build -d` |
| ดู log | `docker compose logs -f [api\|web]` |
| หยุด | `docker compose down` |
| build ใหม่เฉพาะ web | `docker compose build web` |
| build API อย่างเดียว | `docker build -t ai-resume-api .` |
| build web อย่างเดียว | `docker build -f web/Dockerfile.web -t ai-resume-web ./web` |
| ล้าง DB เริ่มใหม่ | `docker compose down && rm ./data/app.db && docker compose up` |

Troubleshooting: `docker build .` ต้องมี `Dockerfile` ที่ root (มีแล้ว) —
ถ้าเจอ `open Dockerfile: no such file` แปลว่ารันผิดโฟลเดอร์;
พอร์ตชนให้ปิด process เก่าที่ฟัง 3000/8000 ก่อน;
build API ครั้งแรก 15–40 นาทีเป็นเรื่องปกติ.

---


#  Future Development

* Personalized learning roadmap
* Interview preparation assistant
* Real-time job market analysis
* Portfolio evaluation
* AI career coach chatbot

---

