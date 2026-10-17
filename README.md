<div align="center">

<img src="web/public/img/logo.svg" alt="Resume AI logo" width="104" height="104">

# Resume AI

**AI-powered resume analyzer that matches your CV against real job postings**

> Upload your resume &rarr; get a fit score, strengths and gaps, plus **3 real jobs** you actually match &mdash; each with a link to the original posting

[![Tests](https://img.shields.io/badge/tests-125%20passed-16a34a)](https://github.com/bimnova001/AI_resume) [![Python](https://img.shields.io/badge/python-3.11-4338ca)](https://www.python.org) [![License](https://img.shields.io/badge/license-MIT-6366f1)](LICENSE)

[Diagram](Architecture.drawio) &middot; [Architecture notes](Architecture.md)

</div>

---

## <img src="web/public/img/icons/spark.svg" width="20"> Highlights

| | Capability |
|---|---|
| <img src="web/public/img/icons/file.svg" width="18"> | **PDF resume analysis** | Validates type and size (<= 10 MB), extracts text with PyMuPDF, deletes the upload immediately |
| <img src="web/public/img/icons/sparkles.svg" width="18"> | **Grounded AI analysis** | BGE-M3 embeddings + an LLM in strict JSON mode (Gemini API or local Qwen GGUF) |
| <img src="web/public/img/icons/target.svg" width="18"> | **Top-3 real jobs** | Pre-filtered by the job title/type you enter, then AI-ranked across only the top 10 candidates |
| <img src="web/public/img/icons/globe.svg" width="18"> | **5 live job sources** | Remotive &middot; Arbeitnow &middot; Remote OK &middot; Jobicy &middot; The Muse &mdash; **zero mock data** |
| <img src="web/public/img/icons/refresh.svg" width="18"> | **Server pulls on its own** | Background scheduler every 6 hours plus a first-run seed; users never press refresh |
| <img src="web/public/img/icons/languages.svg" width="18"> | **10 languages** | EN &middot; TH &middot; ZH &middot; JA &middot; KO &middot; VI &middot; ID &middot; MS &middot; HI &middot; ES |
| <img src="web/public/img/icons/lock.svg" width="18"> | **Accounts &amp; history** | Register/login returns a bearer token; every analysis is stored against the user |
| <img src="web/public/img/icons/chart.svg" width="18"> | **Service dashboard** | Row counts per source, fetch status, live source checks and recent logs |
| <img src="web/public/img/icons/flask.svg" width="18"> | **125 tests** | `pytest tests/ test.py` &mdash; no GPU required |

---

## <img src="web/public/img/icons/rocket.svg" width="20"> Quick start

### Docker (recommended)

```bash
cp .env.example .env      # Windows: copy .env.example .env
docker compose up --build
```

Open **http://localhost:3000** &rarr; API docs at http://localhost:8000/docs

> The first start downloads ~7 GB of models into a Docker volume (slow once, then cached). Budget 16 GB RAM and 20 GB disk.

### Run locally

```bash
pip install -r requirements.txt
python app.py            # starts FastAPI :8000 and Node :3000 together

# open http://localhost:3000
```

---

## <img src="web/public/img/icons/blocks.svg" width="20"> Architecture

```text
User uploads a PDF
        |
        v
Express proxy :3000 ----------> static files + API proxy
        |
        v
FastAPI :8000
   +-- /analyze      validate -> PyMuPDF -> BGE-M3 -> LLM -> matcher
   +-- /jobs         real listings, search, service status
   +-- /auth         register / login -> bearer token
   +-- /translate    translate the analysis into the UI language
   +-- /admin/*      read-only dashboard data
        |
        v
SQLite  jobs - users - analysis_history - saved_jobs - app_logs

Background job service (runs without user interaction)
   scheduler -> 5 job APIs -> normalize + upsert -> SQLite
```

An editable version of this diagram lives in [**`Architecture.drawio`**](Architecture.drawio) (open with [draw.io](https://app.diagrams.net)).

---

## <img src="web/public/img/icons/wrench.svg" width="20"> Tech stack

| Layer | Used for |
|---|---|
| **FastAPI &middot; Uvicorn** | All REST endpoints |
| **PyMuPDF** | PDF text extraction (always closes the file handle) |
| **sentence-transformers &middot; scikit-learn** | BGE-M3 embeddings and cosine similarity |
| **llama-cpp-python** | Runs Qwen2.5-7B GGUF locally on CPU (lazy loaded) |
| **httpx** | Gemini API calls and job feed adapters |
| **SQLite** *(stdlib)* | All persistence &mdash; 6 tables |
| **Express &middot; Multer &middot; Axios** | Node proxy, uploads, backend forwarding |
| **Vanilla JS &middot; i18next** | Frontend with 10 locales (196 keys each) |
| **pytest** | 125 tests |
| **Docker** | `Dockerfile` plus `docker-compose.yml` |

---

## <img src="web/public/img/icons/sliders.svg" width="20"> Configuration

See [`.env.example`](.env.example) for the full list.

| Variable | Default | Meaning |
|---|---|---|
| `LLM_PROVIDER` | `local` | `local` = offline Qwen GGUF &middot; `google` = Gemini API |
| `GOOGLE_API_KEY` | &mdash; | Required when `LLM_PROVIDER=google` |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Model to call (an automatic fallback chain covers retired names) |
| `JOBS_REFRESH_HOURS` | `6` | How often the scheduler refetches postings |
| `JOBS_DIVERSE` | `1` | Rotate across categories (dev/data/design/marketing/&hellip;) |
| `USE_SMALL_EMBEDDING` | `false` | `1` swaps BGE-M3 for MiniLM to save RAM |
| `DB_PATH` | `./data/app.db` | SQLite location |
| `MAX_UPLOAD_MB` | `10` | Maximum upload size |

---

## <img src="web/public/img/icons/flask.svg" width="20"> Tests

```bash
pytest tests/ test.py -v      # 125 tests
```

Covers API validation, PDF parsing, DB schema, job source adapters (mock transport), LLM provider switching plus JSON repair, and i18n key parity across all 10 languages.

---

## <img src="web/public/img/icons/folder.svg" width="20"> Project layout

```text
|-- app.py                 FastAPI routes and startup
|-- logger.py              rotating file + console logging
|-- model/
|   |-- parser.py          PDF -> text
|   |-- embedding.py       BGE-M3 (lazy loaded)
|   |-- llm.py             local Qwen + JSON mode
|   |-- google_llm.py      Gemini provider + model fallback chain
|   |-- matcher.py         resume <-> jobs ranking
|   |-- job_sources.py     5 feed adapters
|   |-- job_service.py     background scheduler
|   |-- database.py        SQLite schema and queries
|   |-- rule.py            resume structure rules
|   +-- jsonutil.py        robust JSON parsing
|-- web/
|   |-- server.js          Express proxy
|   |-- public/            HTML . CSS . JS
|   +-- locales/           10 language files
+-- tests/                 125 tests
```

---

## <img src="web/public/img/icons/globe.svg" width="20"> Job sources

Five feeds, none of them require an API key:

| Source | Focus |
|---|---|
| [Remotive](https://remotive.com) | Remote roles across every category |
| [Arbeitnow](https://www.arbeitnow.com) | Europe-wide listings (Germany-heavy) |
| [Remote OK](https://remoteok.com) | Remote work across many disciplines |
| [Jobicy](https://jobicy.com) | Remote roles tagged by industry |
| [The Muse](https://www.themuse.com) | On-site roles across many countries |

Optional, needs a key: **Adzuna** (`ADZUNA_APP_ID` / `ADZUNA_APP_KEY`) and **Google Jobs** via SerpApi (`SERPAPI_KEY`).

> <img src="web/public/img/icons/alert.svg" width="16"> **LinkedIn and Facebook have no public jobs API.** Reserved adapter slots already exist in `model/job_sources.py`, so dropping in an official integration later needs no changes anywhere else.

Every posting is stored with its **original URL** and **publication date**, and a `UNIQUE(source, external_id)` constraint prevents duplicates across refreshes.

---

## <img src="web/public/img/icons/shield.svg" width="20"> Design notes

- <img src="web/public/img/icons/check.svg" width="14"> **Why the AI never sees the whole job list.** Feeding hundreds of postings to an LLM is slow and expensive. The matcher first filters candidates with cheap SQLite keyword search, then scores only the **top 10** with embeddings.
- <img src="web/public/img/icons/check.svg" width="14"> **Structured output.** The LLM runs in JSON mode with a fixed schema, temperature 0, and one automatic repair retry. If the reply still is not parseable the raw text is shown instead of empty cards.
- <img src="web/public/img/icons/check.svg" width="14"> **Secrets never reach the logs.** Every error message is redacted (`key=REDACTED`), and Gemini failures fall back to the local model when one is already downloaded.
- <img src="web/public/img/icons/check.svg" width="14"> **Uploads do not persist.** Files are written under a random UUID name, processed, and removed in a `finally` block on every path.
- <img src="web/public/img/icons/check.svg" width="14"> **The server owns the data.** The scheduler fetches on its own schedule, so users only ever read.

---

## <img src="web/public/img/icons/chart.svg" width="20"> Service dashboard

Open `/pages/admin.html` for a read-only view of the whole system:

- <img src="web/public/img/icons/check.svg" width="14"> Row counts per table and per job source
- <img src="web/public/img/icons/check.svg" width="14"> When the server last fetched, and whether a fetch is running now
- <img src="web/public/img/icons/check.svg" width="14"> **Live source check** &mdash; pings each feed read-only, nothing is stored
- <img src="web/public/img/icons/check.svg" width="14"> The 10 newest postings with links, plus recent service logs

---

## <img src="web/public/img/icons/languages.svg" width="20"> Multi-language

The interface ships in **10 languages** with 196 keys each. Static markup uses `data-i18n` attributes; JavaScript-rendered strings use `T("key", "English fallback")` so pages still render in English if the i18next CDN is unreachable. Resume analysis is machine-translated into whichever language is selected, and English is the source language.

---

<div align="center">

**Resume AI** &middot; AI Career Navigator

[![FastAPI](https://img.shields.io/badge/FastAPI-4338ca?style=flat-square)](https://fastapi.tiangolo.com) [![MIT](https://img.shields.io/badge/License-MIT-6366f1?style=flat-square)](LICENSE)

</div>
