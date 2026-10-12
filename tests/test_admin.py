"""Unit tests: /admin/* dashboard APIs."""
from fastapi.testclient import TestClient

import app as app_module
from app import app
from model import database as db

client = TestClient(app, raise_server_exceptions=False)


def test_admin_stats_shape():
    db.upsert_job({"title": "A", "source": "remotive", "external_id": "1", "url": "u1"})
    db.upsert_job({"title": "B", "source": "muse", "external_id": "2", "url": "u2"})
    r = client.get("/admin/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["errors"] == {}
    assert body["db"]["tables"]["jobs"] == 2
    assert body["db"]["per_source"] == {"remotive": 1, "muse": 1}
    assert body["jobs_service"]["total"] == 2
    assert "config" in body and "auto_refresh" in body["config"]
    # no secrets leaked
    assert "pw_hash" not in r.text and "salt" not in r.text.replace("asphalt", "")


def test_admin_stats_db_failure_surfaced(monkeypatch):
    def boom():
        raise RuntimeError("disk gone")

    monkeypatch.setattr(db, "_connect", boom)
    r = client.get("/admin/stats")
    assert r.status_code == 200  # still 200, error shown in body
    assert "disk gone" in r.json()["errors"]["db"]


def test_admin_logs():
    db.write_log("evt1", "detail1")
    r = client.get("/admin/logs?limit=5")
    assert r.status_code == 200
    logs = r.json()["logs"]
    assert logs and logs[0]["event"] == "evt1"


def test_admin_source_check_mocked(monkeypatch):
    async def fake_ok(client, limit=3):
        return [{"title": "T", "source": "x", "external_id": "e", "url": "u"}]

    async def fake_down(client, limit=3):
        raise ConnectionError("no net")

    monkeypatch.setitem(app_module.job_sources.FETCHERS, "remotive", fake_ok)
    monkeypatch.setitem(app_module.job_sources.FETCHERS, "arbeitnow", fake_down)
    for key in ("remoteok", "jobicy", "muse"):
        monkeypatch.setitem(app_module.job_sources.FETCHERS, key, fake_ok)

    r = client.get("/admin/source-check")
    assert r.status_code == 200
    src = r.json()["sources"]
    assert src["remotive"]["ok"] is True and src["remotive"]["sample"] == 1
    assert src["arbeitnow"]["ok"] is False and "error" in src["arbeitnow"]
    assert src["adzuna"]["configured"] is False  # no keys in test env
    assert src["linkedin"]["configured"] is False
