"""API tests: /analyze validation+cleanup, /jobs, /auth, /history (heavy AI mocked)."""
import io

import pytest
from fastapi.testclient import TestClient

import app as app_module
from app import app
from model import database as db
from model.parser import PDFExtractError

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def ai_mocked(monkeypatch):
    monkeypatch.setattr(app_module, "extract_pdf", lambda path: "Python AI Engineer resume")
    monkeypatch.setattr(app_module, "calculate_similarity", lambda r, j: 78.5)
    monkeypatch.setattr(
        app_module, "analyze_resume",
        lambda *a, **k: '{"resume_score": 80, "summary": "good"}',
    )
    monkeypatch.setattr(
        app_module.matcher, "suggest_jobs",
        lambda *a, **k: [{"id": 1, "title": "AI Engineer", "company": "Acme",
                          "match": 90.0, "reason": "test", "matched_skills": ["python"],
                          "location": "", "type": "", "salary": "",
                          "url": "", "source": "test", "posted_at": ""}],
    )


@pytest.fixture()
def tmp_uploads(tmp_path, monkeypatch):
    d = tmp_path / "uploads"
    d.mkdir()
    monkeypatch.setattr(app_module, "UPLOAD_DIR", str(d))
    return d


def _pdf(name="resume.pdf", size=100):
    return (name, b"%PDF-1.4\n" + b"x" * size, "application/pdf")


# ---------- /analyze validation ----------

def test_analyze_missing_job_title(tmp_uploads, ai_mocked):
    r = client.post("/analyze", files={"file": _pdf()}, data={"job_title": "  "})
    assert r.status_code == 400


def test_analyze_missing_file(tmp_uploads, ai_mocked):
    r = client.post("/analyze", data={"job_title": "AI Engineer"})
    assert r.status_code in (400, 422)


def test_analyze_rejects_non_pdf(tmp_uploads, ai_mocked):
    r = client.post("/analyze",
                    files={"file": ("resume.txt", b"hi", "text/plain")},
                    data={"job_title": "AI Engineer"})
    assert r.status_code == 415


def test_analyze_rejects_oversize(tmp_uploads, ai_mocked, monkeypatch):
    monkeypatch.setattr(app_module, "MAX_UPLOAD_BYTES", 10)
    r = client.post("/analyze", files={"file": _pdf(size=100)},
                    data={"job_title": "AI Engineer"})
    assert r.status_code == 413
    assert list(tmp_uploads.iterdir()) == []


def test_analyze_empty_text_422(tmp_uploads, monkeypatch):
    monkeypatch.setattr(
        app_module, "extract_pdf",
        lambda path: (_ for _ in ()).throw(PDFExtractError("No extractable text found")),
    )
    monkeypatch.setattr(app_module, "calculate_similarity", lambda r, j: 0)
    r = client.post("/analyze", files={"file": _pdf()}, data={"job_title": "AI Engineer"})
    assert r.status_code == 422


def test_analyze_happy_path_and_cleanup(tmp_uploads, ai_mocked):
    r = client.post("/analyze", files={"file": _pdf()},
                    data={"job_title": "AI Engineer", "language": "en"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["job_match"] == 78.5
    assert body["analysis"] == {"resume_score": 80, "summary": "good"}
    assert body["history_id"] is not None  # anonymous history still recorded
    assert body["suggested_jobs"][0]["title"] == "AI Engineer"
    assert body["analysis_parse_ok"] is True
    assert list(tmp_uploads.iterdir()) == []  # no leftover files


def test_analyze_long_title_rejected(tmp_uploads, ai_mocked):
    r = client.post("/analyze", files={"file": _pdf()},
                    data={"job_title": "x" * 500})
    assert r.status_code == 400


def test_analyze_provider_failure_is_502(tmp_uploads, monkeypatch):
    monkeypatch.setattr(app_module, "extract_pdf", lambda path: "resume text")
    monkeypatch.setattr(app_module, "calculate_similarity", lambda r, j: 50.0)

    def boom(*a, **k):
        raise RuntimeError("Gemini request failed after 3 tries (model=x)")

    monkeypatch.setattr(app_module, "analyze_resume", boom)
    monkeypatch.setattr(app_module.matcher, "suggest_jobs", lambda *a, **k: [])
    r = client.post("/analyze", files={"file": _pdf()},
                    data={"job_title": "AI Engineer"})
    assert r.status_code == 502
    assert "unavailable" in r.json()["detail"]


# ---------- jobs ----------

def test_jobs_crud_and_404():
    assert client.get("/jobs").json()["total"] == 0
    jid = db.upsert_job({"title": "AI Engineer", "company": "Acme",
                         "source": "t", "external_id": "1",
                         "location": "Bangkok", "url": "https://x/1"})
    assert client.get("/jobs?q=acme").json()["total"] == 1
    assert client.get("/jobs?job_type=zzz-no-match").json()["total"] == 0
    assert client.get(f"/jobs/{jid}").json()["title"] == "AI Engineer"
    assert client.get("/jobs/99999").status_code == 404


def test_jobs_refresh_mocked(monkeypatch):
    async def fake_refresh(limit_per_source=50):
        db.upsert_job({"title": "R", "source": "s", "external_id": "e", "url": "u"})
        return {"s": 1}

    monkeypatch.setattr(app_module.job_sources, "refresh_jobs", fake_refresh)
    r = client.post("/jobs/refresh", json={"limit_per_source": 5})
    assert r.status_code == 200
    assert r.json()["counts"] == {"s": 1}


# ---------- auth / history / saved ----------

def _register(name="U", email="u@example.com", pw="password123"):
    return client.post("/auth/register",
                       json={"name": name, "email": email, "password": pw})


def test_auth_full_flow(tmp_uploads, ai_mocked):
    assert _register().status_code == 200
    assert _register().status_code == 400  # duplicate
    assert client.post("/auth/register",
                       json={"name": "X", "email": "x@example.com",
                             "password": "short"}).status_code == 400

    login = client.post("/auth/login",
                        json={"email": "u@example.com", "password": "password123"})
    assert login.status_code == 200
    token = login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    assert client.post("/auth/login",
                       json={"email": "u@example.com",
                             "password": "nope-nope-1"}).status_code == 401
    assert client.get("/me").status_code == 401
    assert client.get("/me", headers=headers).json()["email"] == "u@example.com"

    # analysis with token -> linked history
    r = client.post("/analyze", files={"file": _pdf()},
                    data={"job_title": "AI Engineer"}, headers=headers)
    assert r.status_code == 200 and r.json()["history_id"] is not None
    hist = client.get("/history", headers=headers).json()["history"]
    assert len(hist) == 1 and hist[0]["job_title"] == "AI Engineer"

    jid = db.upsert_job({"title": "J", "source": "s", "external_id": "e", "url": "u"})
    assert client.post(f"/jobs/{jid}/save", headers=headers).status_code == 200
    assert client.post("/jobs/99999/save", headers=headers).status_code == 404
    saved = client.get("/saved-jobs", headers=headers).json()["jobs"]
    assert len(saved) == 1

    assert client.post("/auth/logout", headers=headers).status_code == 200
    assert client.get("/me", headers=headers).status_code == 401


def test_translate_degrades_gracefully():
    r = client.post("/translate", json={"text": "hello", "target_lang": "th"})
    assert r.status_code == 200
    assert "translatedText" in r.json()
