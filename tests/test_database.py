"""Unit tests: model.database (jobs, auth, history, saved, logs)."""
import pytest

from model import database as db


def _job(**kw):
    base = {"title": "AI Engineer", "company": "Acme", "source": "test",
            "external_id": "x1", "url": "https://example.com/1"}
    base.update(kw)
    return base


def test_job_upsert_and_list():
    db.upsert_job(_job())
    db.upsert_job(_job(external_id="x2", title="Data Scientist", location="Remote"))
    out = db.list_jobs()
    assert out["total"] == 2
    # newest first
    assert out["jobs"][0]["title"] == "Data Scientist"


def test_job_upsert_updates_existing():
    db.upsert_job(_job())
    db.upsert_job(_job(title="Senior AI Engineer"))
    out = db.list_jobs()
    assert out["total"] == 1
    assert out["jobs"][0]["title"] == "Senior AI Engineer"


def test_job_filters():
    db.upsert_job(_job(external_id="a", title="AI Engineer", location="Bangkok"))
    db.upsert_job(_job(external_id="b", title="Designer", location="Remote", source="other"))
    assert db.list_jobs(q="designer")["total"] == 1
    assert db.list_jobs(location="bangkok")["total"] == 1
    assert db.list_jobs(source="other")["total"] == 1
    assert db.list_jobs(job_type="full")["total"] == 0
    db.upsert_job(_job(external_id="c", title="PM", type="Full-time"))
    assert db.list_jobs(job_type="full-time")["total"] == 1
    limited = db.list_jobs(limit=1)
    assert limited["total"] == 3 and len(limited["jobs"]) == 1


def test_job_requires_title():
    with pytest.raises(ValueError):
        db.upsert_job({"company": "No title"})


def test_get_job_missing():
    assert db.get_job(9999) is None


def test_auth_register_login_flow():
    user = db.create_user("Test User", "Test@Example.com", "password123")
    assert user["email"] == "test@example.com"  # normalized
    authed = db.verify_user("test@example.com", "password123")
    assert authed and authed["id"] == user["id"]
    assert db.verify_user("test@example.com", "wrong") is None
    assert db.verify_user("nobody@example.com", "password123") is None
    token = db.create_session(user["id"])
    me = db.get_user_by_token(token)
    assert me["email"] == "test@example.com"
    db.delete_session(token)
    assert db.get_user_by_token(token) is None


def test_auth_duplicate_and_short_password():
    db.create_user("A", "a@example.com", "password123")
    with pytest.raises(ValueError):
        db.create_user("B", "a@example.com", "password123")
    with pytest.raises(ValueError):
        db.create_user("B", "b@example.com", "short")
    with pytest.raises(ValueError):
        db.create_user("", "c@example.com", "password123")


def test_history_and_saved_jobs():
    user = db.create_user("H", "h@example.com", "password123")
    assert db.list_history(user["id"]) == []
    hid = db.save_analysis(user["id"], "AI Engineer", "ml", 78.5, 80.0, "en")
    assert hid is not None
    hist = db.list_history(user["id"])
    assert len(hist) == 1 and hist[0]["job_title"] == "AI Engineer"

    jid = db.upsert_job(_job())
    db.save_job_for_user(user["id"], jid)
    db.save_job_for_user(user["id"], jid)  # idempotent
    saved = db.list_saved_jobs(user["id"])
    assert len(saved) == 1 and saved[0]["id"] == jid
    with pytest.raises(ValueError):
        db.save_job_for_user(user["id"], 9999)


def test_write_log_never_raises():
    db.write_log("evt", "detail")
    db.write_log("evt2", user_id=12345)  # orphan user id is fine (no FK enforcement)
