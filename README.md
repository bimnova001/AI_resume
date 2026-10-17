<div align="center">

<img src="web/public/img/logo.svg" alt="Resume AI logo" width="104" height="104">

# Resume AI

**แพลตฟอร์มวิเคราะห์เรซูเม่ด้วย AI ที่เชื่อมกับประกาศงานจริง**

> อัปโหลดเรซูเม์ → ได้คะแนนความพร้อม จุดแข็ง/จุดอ่อน และ **งานจริง 3 ตำแหน่ง** ที่เข้าเกณฑ์ พร้อมลิงก์สมัครงาน

[![Tests](https://img.shields.io/badge/tests-125%20passed-16a34a)](https://github.com/bimnova001/AI_resume) [![Python](https://img.shields.io/badge/python-3.11-4338ca)](https://www.python.org) [![License](https://img.shields.io/badge/license-MIT-6366f1)](LICENSE)

[ภาษาไทย](#-ภาษาไทย) &middot; [English](#-english) &middot; [Diagram](Architecture.drawio) &middot; [Architecture](Architecture.md)

</div>

---

## <img src="web/public/img/icons/spark.svg" width="20"> จุดเด่น

| | ความสามารถ |
|---|---|
| <img src="web/public/img/icons/file.svg" width="18"> | **วิเคราะห์เรซูเม์ PDF** | ตรวจไฟล์ ขนาด &le; 10 MB &middot; ดึงข้อความด้วย PyMuPDF &middot; ลบไฟล์ทิ้งทันที |
| <img src="web/public/img/icons/sparkles.svg" width="18"> | **AI วิเคราะห์เชิงลึก** | BGE-M3 embedding + LLM โหมด JSON (Gemini API หรือ Qwen GGUF) |
| <img src="web/public/img/icons/target.svg" width="18"> | **แนะนำงานจริง 3 งาน** | คัดกรองด้วย job title/type ที่กรอก &rarr; ให้ AI คิดคะแนนเฉพาะ 10 อันดับแรก |
| <img src="web/public/img/icons/globe.svg" width="18"> | **ประกาศงานจริง 5 แหล่ง** | Remotive &middot; Arbeitnow &middot; Remote OK &middot; Jobicy &middot; The Muse &mdash; **ไม่มี Mock Data** |
| <img src="web/public/img/icons/refresh.svg" width="18"> | **Server ดึงข้อมูลเอง** | Scheduler ดึงทุก 6 ชม. + seed ตอนเปิดครั้งแรก ผู้ใช้ไม่ต้องกดรีเฟรช |
| <img src="web/public/img/icons/languages.svg" width="18"> | **10 ภาษา** | EN &middot; TH &middot; ZH &middot; JA &middot; KO &middot; VI &middot; ID &middot; MS &middot; HI &middot; ES |
| <img src="web/public/img/icons/lock.svg" width="18"> | **บัญชีผู้ใช้** | Register/Login &rarr; Bearer token &rarr; ประวัติการวิเคราะห์ + งานที่บันทึก |
| <img src="web/public/img/icons/chart.svg" width="18"> | **หน้า Service Dashboard** | ดูจำนวนงานใน DB &middot; สถานะการดึง &middot; เช็ค source สด &middot; อ่าน log |
| <img src="web/public/img/icons/flask.svg" width="18"> | **125 tests** | `pytest tests/ test.py` &mdash; ไม่ต้องมี GPU |

---

## <img src="web/public/img/icons/rocket.svg" width="20"> เริ่มใช้งาน

### แบบ Docker (แนะนำ)

```bash
cp .env.example .env      # Windows: copy .env.example .env
docker compose up --build
```

เปิด **http://localhost:3000** &rarr; API docs ที่ http://localhost:8000/docs

> ครั้งแรกจะดาวน์โหลดโมเดล ~7 GB ลง volume (ช้าเฉพาะครั้งแรก) &middot; ต้อง RAM 16 GB / ดิสก์ 20 GB

### แบบรันเอง

```bash
pip install -r requirements.txt
python app.py            # เปิด FastAPI :8000 + Node :3000 พร้อมกัน
```

---

## <img src="web/public/img/icons/blocks.svg" width="20"> สถาปัตยกรรม

```text
ผู้ใช้อัปโหลด PDF
        |
        v
Express Proxy :3000 ----------> Node proxy + static files
        |
        v
FastAPI :8000
   +-- /analyze      ตรวจไฟล์ -> PyMuPDF -> BGE-M3 -> LLM -> Matcher
   +-- /jobs         รายการงานจริง + ค้นหา + สถานะ service
   +-- /auth         register / login -> Bearer token
   +-- /translate    แปลผลวิเคราะห์เป็นภาษาที่ผู้ใช้เลือก
        |
        v
SQLite  jobs - users - analysis_history - saved_jobs - app_logs

Background Job Service (ทำงานเบื้องหลัง)
   Scheduler -> 5 Job APIs -> normalize + upsert -> SQLite
```

ดูแผนผังแบบแก้ไขได้ที่ **[`Architecture.drawio`](Architecture.drawio)** (เปิดด้วย [draw.io](https://app.diagrams.net))

---

## <img src="web/public/img/icons/wrench.svg" width="20"> เทคสแต็ก

| ชั้น | ใช้ทำอะไร |
|---|---|
| **FastAPI &middot; Uvicorn** | REST API ทั้งหมด |
| **PyMuPDF** | สกัดข้อความจาก PDF (ปิด handle ทุกครั้ง) |
| **sentence-transformers &middot; scikit-learn** | BGE-M3 embedding + cosine similarity |
| **llama-cpp-python** | รัน Qwen2.5-7B GGUF บน CPU (lazy-load) |
| **httpx** | เรียก Gemini API + job feeds |
| **SQLite** *(stdlib)* | เก็บข้อมูลทั้งหมด 6 ตาราง |
| **Express &middot; Multer &middot; Axios** | Node proxy + อัปโหลดไฟล์ |
| **Vanilla JS &middot; i18next** | หน้าเว็บ 10 ภาษา (196 keys/ภาษา) |
| **pytest** | 125 tests |
| **Docker** | `Dockerfile` + `docker-compose.yml` |

---

## <img src="web/public/img/icons/sliders.svg" width="20"> ตัวแปรสำคัญ

ดูครบทุกตัวใน [`.env.example`](.env.example)

| ตัวแปร | ค่าเริ่มต้น | ความหมาย |
|---|---|---|
| `LLM_PROVIDER` | `local` | `local` = Qwen GGUF ออฟไลน์ &middot; `google` = Gemini API |
| `GOOGLE_API_KEY` | — | จำเป็นเมื่อใช้ `LLM_PROVIDER=google` |
| `GEMINI_MODEL` | `gemini-2.5-flash` | รุ่นที่เรียกใช้ (มี fallback chain อัตโนมัติ) |
| `JOBS_REFRESH_HOURS` | `6` | รอบเวลาดึงประกาศงาน |
| `JOBS_DIVERSE` | `1` | ดึงหลายด้าน (dev/data/design/marketing/…) |
| `USE_SMALL_EMBEDDING` | `false` | `1` = ใช้ MiniLM แทน BGE-M3 (ประหยัด RAM) |
| `DB_PATH` | `./data/app.db` | ตำแหน่งฐานข้อมูล |
| `MAX_UPLOAD_MB` | `10` | ขนาดไฟล์สูงสุด |

---

## <img src="web/public/img/icons/flask.svg" width="20"> เทสต์

```bash
pytest tests/ test.py -v      # 125 tests
```

ครอบคลุม: API validation &middot; PDF parsing &middot; DB schema &middot; job sources (mock transport) &middot; LLM provider + repair retry &middot; i18n key parity ทั้ง 10 ภาษา

---

## <img src="web/public/img/icons/folder.svg" width="20"> โครงสร้างโปรเจกต์

```text
|-- app.py                 FastAPI routes + startup
|-- logger.py              rotating file + console logging
|-- model/
|   |-- parser.py          PDF -> text
|   |-- embedding.py       BGE-M3 (lazy)
|   |-- llm.py             local Qwen + JSON mode
|   |-- google_llm.py      Gemini provider + model fallback chain
|   |-- matcher.py         resume <-> jobs ranking
|   |-- job_sources.py     5 feed adapters
|   |-- job_service.py     background scheduler
|   |-- database.py        SQLite schema + queries
|   |-- rule.py            resume structure rules
|   +-- jsonutil.py        robust JSON parsing
|-- web/
|   |-- server.js          Express proxy
|   |-- public/            HTML . CSS . JS
|   +-- locales/           10 ภาษา
+-- tests/                 125 tests
```

---

<div align="center">

**Resume AI** &middot; AI Career Navigator

[![FastAPI](https://img.shields.io/badge/FastAPI-4338ca?style=flat-square)](https://fastapi.tiangolo.com) [![MIT](https://img.shields.io/badge/License-MIT-6366f1?style=flat-square)](LICENSE)

</div>

---

# - ภาษาไทย

**Resume AI** คือแพลตฟอร์มช่วยนักศึกษาและผู้จบใหม่วิเคราะห์เรซูเม่เทียบกับตำแหน่งงานจริง แล้วแนะนำงานที่เหมาะกับทักษะของตัวเอง

### ขั้นตอนการทำงาน

1. **อัปโหลด PDF** — ระบบตรวจชนิดไฟล์และขนาด (สูงสุด 10 MB) แล้วลบไฟล์ทิ้งทันทีหลังประมวลผล
2. **ดึงข้อความ** — PyMuPDF อ่านข้อความ พร้อมตรวจว่าเป็น PDF จริง ไม่ใช่ไฟล์เข้ารหัสหรือภาพสแกน
3. **วัดความพร้อม** — BGE-M3 แปลงเรซูเม่เป็นเวกเตอร์ เทียบกับตำแหน่งที่ต้องการด้วย cosine similarity
4. **ให้ AI วิเคราะห์** — LLM ประเมินจุดแข็ง จุดอ่อน ทักษะที่ขาด โครงการที่ควรทำ และเส้นทางอาชีพ
5. **เลือกงานจริง 3 ตำแหน่ง** — ค้นงานที่ตรงกับ job title/type ที่กรอก จากนั้นให้ AI จัดอันดับเฉพาะ 10 งานแรก

### <img src="web/public/img/icons/database.svg" width="18"> ข้อมูลงานจริง

ระบบดึงประกาศงานจาก **5 แหล่งที่ไม่ต้องใช้ API key**:

| แหล่ง | ลักษณะงาน |
|---|---|
| [Remotive](https://remotive.com) | Remote ทุกสาขาอาชีพ |
| [Arbeitnow](https://www.arbeitnow.com) | งานทั่วยุโรป (เน้นเยอรมนี) |
| [Remote OK](https://remoteok.com) | Remote หลากหลายสาขา |
| [Jobicy](https://jobicy.com) | Remote พร้อมแท็กอุตสาหกรรม |
| [The Muse](https://www.themuse.com) | งานประจำหลายประเทศ |

เพิ่มเติมได้ถ้ามี key: **Adzuna** (`ADZUNA_APP_ID`/`ADZUNA_APP_KEY`) และ **Google Jobs** ผ่าน SerpApi (`SERPAPI_KEY`)

> <img src="web/public/img/icons/alert.svg" width="16"> **LinkedIn / Facebook** ไม่มี API สาธารณะ — โค้ดเตรียมจุดเสียบไว้ใน `model/job_sources.py` แล้ว เมื่อมีสิทธิ์เข้าถึงจะเติมฟังก์ชันได้เลยโดยไม่ต้องแก้ส่วนอื่น

ทุกประกาศถูกเก็บลง SQLite พร้อม **ลิงก์ต้นฉบับ** และ **วันที่ประกาศ** โดยมี `UNIQUE(source, external_id)` กันข้อมูลซ้ำ

### <img src="web/public/img/icons/chart.svg" width="18"> หน้า Service Dashboard

เปิด `/pages/admin.html` เพื่อดูภาพรวมระบบ:

- <img src="web/public/img/icons/check.svg" width="14"> จำนวนงานในฐานข้อมูล และแยกตามแหล่ง
- <img src="web/public/img/icons/check.svg" width="14"> วันที่ดึงข้อมูลล่าสุด + กำลังดึงอยู่หรือไม่
- <img src="web/public/img/icons/check.svg" width="14"> **ปุ่มเช็ค sources สด** — ยิงทดสอบทีละแหล่งแบบ read-only
- <img src="web/public/img/icons/check.svg" width="14"> 10 ประกาศล่าสุดพร้อมลิงก์ + service log

### <img src="web/public/img/icons/shield.svg" width="18"> ความปลอดภัยที่ใส่ไว้

- <img src="web/public/img/icons/check.svg" width="14"> API key ถูก **redact** ออกจากทุก error log (`key=REDACTED`)
- <img src="web/public/img/icons/check.svg" width="14"> ถ้า Gemini ล่ม ระบบจะ fallback ไปใช้โมเดลในเครื่องอัตโนมัติ (ถ้ามีไฟล์พร้อม)
- <img src="web/public/img/icons/check.svg" width="14"> ผู้ใช้ต้อง login เพื่อบันทึกประวัติและงานที่ชอบ

---

# - English

**Resume AI** helps students and fresh graduates compare their resume against real job postings and get matched roles they can actually apply to.

### How it works

1. **Upload PDF** — validated for type and size (<= 10 MB), deleted right after processing
2. **Extract text** — PyMuPDF, rejecting encrypted or image-only scans
3. **Score fit** — BGE-M3 embeddings + cosine similarity against the target role
4. **AI analysis** — LLM returns strengths, weaknesses, missing skills, projects and career paths in strict JSON mode
5. **Top-3 real jobs** — pre-filtered by the job title/type you entered, then AI-ranked across only the top 10 candidates

### Why the AI never sees everything

Sending hundreds of postings to an LLM is slow and expensive. The matcher filters candidates with cheap SQLite keyword search first, then scores just **10 jobs** with embeddings. That keeps `/analyze` fast while still picking the best 3 matches.

### Multi-language

The UI ships in **10 languages** with 196 keys each. Static text uses `data-i18n` attributes; JavaScript-rendered strings use `T("key", "English fallback")` so the page still works if the i18next CDN is unreachable. Resume analysis is machine-translated to the language you select.

### License

MIT — see [LICENSE](LICENSE).
