<div align="center">

<img src="web/public/img/logo.svg" alt="Resume AI logo" width="104" height="104">

# Resume AI

**แพลตฟอร์มวิเคราะห์เรซูเม่ด้วย AI ที่เชื่อมกับประกาศงานจริง**

> อัปโหลดเรซูเม์ → ได้คะแนนความพร้อม จุดแข็ง/จุดอ่อน และ **งานจริง 3 ตำแหน่ง** ที่เข้าเกณฑ์ พร้อมลิงก์สมัครงาน

[![Tests](https://img.shields.io/badge/tests-125%20passed-16a34a)](https://github.com/bimnova001/AI_resume) [![Python](https://img.shields.io/badge/python-3.11-4338ca)](https://www.python.org) [![License](https://img.shields.io/badge/license-MIT-6366f1)](LICENSE)

[ภาษาไทย](#-ภาษาไทย) &middot; [English](#-english) &middot; [Diagram](Architecture.drawio) &middot; [Architecture](Architecture.md)

</div>

---

## <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" vertical-align="-3px"><path d="M12 2.5l2.3 6.1 6.2 2.4-6.2 2.4L12 19.5l-2.3-6.1L3.5 11l6.2-2.4z"/></svg> จุดเด่น

| | ความสามารถ |
|---|---|
| <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4338ca" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" vertical-align="-3px"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M16 13H8"/><path d="M16 17H8"/></svg> | **วิเคราะห์เรซูเม์ PDF** | ตรวจไฟล์ ขนาด &le; 10 MB &middot; ดึงข้อความด้วย PyMuPDF &middot; ลบไฟล์ทิ้งทันที |
| <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4338ca" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" vertical-align="-3px"><path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M18.5 15.5l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8z"/></svg> | **AI วิเคราะห์เชิงลึก** | BGE-M3 embedding + LLM โหมด JSON (Gemini API หรือ Qwen GGUF) |
| <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4338ca" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" vertical-align="-3px"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.6"/></svg> | **แนะนำงานจริง 3 งาน** | คัดกรองด้วย job title/type ที่กรอก &rarr; ให้ AI คิดคะแนนเฉพาะ 10 อันดับแรก |
| <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4338ca" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" vertical-align="-3px"><circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3c2.5 2.5 3.8 5.6 3.8 9S14.5 18.5 12 21c-2.5-2.5-3.8-5.6-3.8-9S9.5 5.5 12 3z"/></svg> | **ประกาศงานจริง 5 แหล่ง** | Remotive &middot; Arbeitnow &middot; Remote OK &middot; Jobicy &middot; The Muse &mdash; **ไม่มี Mock Data** |
| <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4338ca" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" vertical-align="-3px"><path d="M20.5 12a8.5 8.5 0 1 1-2.6-6.1"/><path d="M21 3.5V9h-5.5"/></svg> | **Server ดึงข้อมูลเอง** | Scheduler ดึงทุก 6 ชม. + seed ตอนเปิดครั้งแรก ผู้ใช้ไม่ต้องกดรีเฟรช |
| <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4338ca" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" vertical-align="-3px"><path d="M2.5 5.5h9"/><path d="M7 3.2v2.3c0 4-2 7-4.5 8"/><path d="M5 11.3c1.5 2 4 3.4 6.4 3.9"/><path d="M12.5 21l4.6-11L21.7 21"/><path d="M14.4 17h5.4"/></svg> | **10 ภาษา** | EN &middot; TH &middot; ZH &middot; JA &middot; KO &middot; VI &middot; ID &middot; MS &middot; HI &middot; ES |
| <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4338ca" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" vertical-align="-3px"><rect x="4" y="10" width="16" height="10" rx="2"/><path d="M8 10V7a4 4 0 1 1 8 0v3"/></svg> | **บัญชีผู้ใช้** | Register/Login &rarr; Bearer token &rarr; ประวัติการวิเคราะห์ + งานที่บันทึก |
| <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4338ca" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" vertical-align="-3px"><path d="M4 20V11"/><path d="M10 20V4"/><path d="M16 20v-6"/><path d="M2 20h20"/></svg> | **หน้า Service Dashboard** | ดูจำนวนงานใน DB &middot; สถานะการดึง &middot; เช็ค source สด &middot; อ่าน log |
| <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4338ca" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" vertical-align="-3px"><path d="M9.5 3h5"/><path d="M10.5 3v6L5.6 18.4A2 2 0 0 0 7.3 21.4h9.4a2 2 0 0 0 1.7-3L13.5 9V3"/><path d="M7.6 15h8.8"/></svg> | **125 tests** | `pytest tests/ test.py` &mdash; ไม่ต้องมี GPU |

---

## <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" vertical-align="-3px"><path d="M5.5 14c-1.6 1.6-2.1 5-2.1 5s3.4-.5 5-2.1a2 2 0 0 0-2.9-2.9z"/><path d="M12.4 14.8l-3.2-3.2a12 12 0 0 1 3-6c2.5-2.5 6.3-2.9 6.3-2.9s-.4 3.8-2.9 6.3a12 12 0 0 1-6 3z"/><circle cx="14.5" cy="9.5" r="1.3"/></svg> เริ่มใช้งาน

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

## <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" vertical-align="-3px"><rect x="3" y="3" width="7.5" height="7.5" rx="1.5"/><rect x="13.5" y="3" width="7.5" height="7.5" rx="1.5"/><rect x="3" y="13.5" width="7.5" height="7.5" rx="1.5"/><path d="M17 14v7M13.5 17.5h7"/></svg> สถาปัตยกรรม

```text
ผู้ใช้อัปโหลด PDF
        ↓
Express Proxy :3000 ──────────► Node proxy + static files
        ↓
FastAPI :8000
   ├─ /analyze      ตรวจไฟล์ → PyMuPDF → BGE-M3 → LLM → Matcher
   ├─ /jobs         รายการงานจริง + ค้นหา + สถานะ service
   ├─ /auth         register / login → Bearer token
   └─ /translate    แปลผลวิเคราะห์เป็นภาษาที่ผู้ใช้เลือก
        ↓
SQLite  jobs · users · analysis_history · saved_jobs · app_logs

Background Job Service (ทำงานเบื้องหลัง)
   Scheduler → 5 Job APIs → normalize + upsert → SQLite
```

ดูแผนผังแบบแก้ไขได้ที่ **[`Architecture.drawio`](Architecture.drawio)** (เปิดด้วย [draw.io](https://app.diagrams.net))

---

## <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" vertical-align="-3px"><path d="M20.3 5.7a5 5 0 0 1-6.9 6.4L5.6 20a2 2 0 0 1-2.8-2.8l7.9-7.9a5 5 0 0 1 6.4-6.9l-3 3 1.4 1.4z"/></svg> เทคสแต็ก

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

## <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" vertical-align="-3px"><path d="M4 21v-6"/><path d="M4 11V3"/><path d="M12 21v-8"/><path d="M12 9V3"/><path d="M20 21v-4"/><path d="M20 13V3"/><path d="M1.5 15h5"/><path d="M9.5 9h5"/><path d="M17.5 17h5"/></svg> ตัวแปรสำคัญ

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

## <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" vertical-align="-3px"><path d="M9.5 3h5"/><path d="M10.5 3v6L5.6 18.4A2 2 0 0 0 7.3 21.4h9.4a2 2 0 0 0 1.7-3L13.5 9V3"/><path d="M7.6 15h8.8"/></svg> เทสต์

```bash
pytest tests/ test.py -v      # 125 tests
```

ครอบคลุม: API validation &middot; PDF parsing &middot; DB schema &middot; job sources (mock transport) &middot; LLM provider + repair retry &middot; i18n key parity ทั้ง 10 ภาษา

---

## <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" vertical-align="-3px"><path d="M3 7a2 2 0 0 1 2-2h3.8l2 2H19a2 2 0 0 1 2 2v8.5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg> โครงสร้างโปรเจกต์

```text
├── app.py                 FastAPI routes + startup
├── logger.py              rotating file + console logging
├── model/
│   ├── parser.py          PDF → text
│   ├── embedding.py       BGE-M3 (lazy)
│   ├── llm.py             local Qwen + JSON mode
│   ├── google_llm.py      Gemini provider + model fallback chain
│   ├── matcher.py         resume ↔ jobs ranking
│   ├── job_sources.py     5 feed adapters
│   ├── job_service.py     background scheduler
│   ├── database.py        SQLite schema + queries
│   ├── rule.py            resume structure rules
│   └── jsonutil.py        robust JSON parsing
├── web/
│   ├── server.js          Express proxy
│   ├── public/            HTML · CSS · JS
│   └── locales/           10 ภาษา
└── tests/                 125 tests
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

### <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4338ca" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" vertical-align="-3px"><ellipse cx="12" cy="5.5" rx="8" ry="3"/><path d="M4 5.5v13c0 1.7 3.6 3 8 3s8-1.3 8-3v-13"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/></svg> ข้อมูลงานจริง

ระบบดึงประกาศงานจาก **5 แหล่งที่ไม่ต้องใช้ API key**:

| แหล่ง | ลักษณะงาน |
|---|---|
| [Remotive](https://remotive.com) | Remote ทุกสาขาอาชีพ |
| [Arbeitnow](https://www.arbeitnow.com) | งานทั่วยุโรป (เน้นเยอรมนี) |
| [Remote OK](https://remoteok.com) | Remote หลากหลายสาขา |
| [Jobicy](https://jobicy.com) | Remote พร้อมแท็กอุตสาหกรรม |
| [The Muse](https://www.themuse.com) | งานประจำหลายประเทศ |

เพิ่มเติมได้ถ้ามี key: **Adzuna** (`ADZUNA_APP_ID`/`ADZUNA_APP_KEY`) และ **Google Jobs** ผ่าน SerpApi (`SERPAPI_KEY`)

> <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" vertical-align="-3px"><path d="M10.3 3.9L1.9 18a2 2 0 0 0 1.7 3h16.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9.5v4"/><path d="M12 17.2h.01"/></svg> **LinkedIn / Facebook** ไม่มี API สาธารณะ — โค้ดเตรียมจุดเสียบไว้ใน `model/job_sources.py` แล้ว เมื่อมีสิทธิ์เข้าถึงจะเติมฟังก์ชันได้เลยโดยไม่ต้องแก้ส่วนอื่น

ทุกประกาศถูกเก็บลง SQLite พร้อม **ลิงก์ต้นฉบับ** และ **วันที่ประกาศ** โดยมี `UNIQUE(source, external_id)` กันข้อมูลซ้ำ

### <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4338ca" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" vertical-align="-3px"><path d="M4 20V11"/><path d="M10 20V4"/><path d="M16 20v-6"/><path d="M2 20h20"/></svg> หน้า Service Dashboard

เปิด `/pages/admin.html` เพื่อดูภาพรวมระบบ:

- จำนวนงานในฐานข้อมูล และแยกตามแหล่ง
- วันที่ดึงข้อมูลล่าสุด + กำลังดึงอยู่หรือไม่
- **ปุ่มเช็ค sources สด** — ยิงทดสอบทีละแหล่งแบบ read-only
- 10 ประกาศล่าสุดพร้อมลิงก์ + service log

### <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4338ca" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" vertical-align="-3px"><path d="M12 3l8 2.8v6.1c0 4.8-3.3 7.6-8 9.1-4.7-1.5-8-4.3-8-9.1V5.8z"/><path d="M9 12l2 2 4-4"/></svg> ความปลอดภัยที่ใส่ไว้

- API key ถูก **redact** ออกจากทุก error log (`key=REDACTED`)
- ถ้า Gemini ล่ม ระบบจะ fallback ไปใช้โมเดลในเครื่องอัตโนมัติ (ถ้ามีไฟล์พร้อม)
- ผู้ใช้ต้อง login เพื่อบันทึกประวัติและงานที่ชอบ

---

# - English

**Resume AI** helps students and fresh graduates compare their resume against real job postings and get matched roles they can actually apply to.

### How it works

1. **Upload PDF** — validated for type and size (≤ 10 MB), deleted right after processing
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
