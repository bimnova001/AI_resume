"""Unit tests: model.job_service + meta + /jobs/status + refresh guard."""
import asyncio

import pytest
from fastapi.testclient import TestClient

import app as app_module
from app import app
from model import database as db
from model import job_service

client = TestClient(app, raise_server_exceptions=False)


def test_meta_roundtrip():
    assert db.get_meta("missing") == ""
    db.set_meta("k", "v")
    assert db.get_meta("k") == "v"


def test_refresh_now_success_updates_status(monkeypatch):
    async def fake_refresh(limit_per_source=50):
        db.upsert_job({"title": "Svc", "source": "s", "external_id": "e", "url": "u"})
        return {"s": 1}

    monkeypatch.setattr(app_module.job_sources, "refresh_jobs", fake_refresh)
    out = asyncio.run(job_service.refresh_now(limit_per_source=5))
    assert out["status"] == "success"
    assert out["counts"] == {"s": 1} and out["total"] == 1
    st = job_service.get_status()
    assert st["total"] == 1 and st["refreshing"] is False
    assert st["last_refresh_at"]
    assert st["last_counts"] == {"s": 1}


def test_refresh_concurrent_guard(monkeypatch):
    started = asyncio.Event()
    release = asyncio.Event()

    async def slow_refresh(limit_per_source=50):
        started.set()
        await release.wait()
        return {"s": 1}

    monkeypatch.setattr(app_module.job_sources, "refresh_jobs", slow_refresh)

    async def go():
        t1 = asyncio.create_task(job_service.refresh_now())
        await started.wait()
        second = await job_service.refresh_now()
        release.set()
        first = await t1
        return first, second

    first, second = asyncio.run(go())
    assert first["status"] == "success"
    assert second["status"] == "already_running"


def test_jobs_status_endpoint():
    r = client.get("/jobs/status")
    assert r.status_code == 200
    body = r.json()
    assert {"total", "refreshing", "last_refresh_at", "last_counts"} <= set(body)


def test_api_refresh_already_running(monkeypatch):
    monkeypatch.setattr(job_service, "_running", True)
    r = client.post("/jobs/refresh", json={"limit_per_source": 5})
    assert r.status_code == 200
    assert r.json()["status"] == "already_running"
    monkeypatch.setattr(job_service, "_running", False)


def test_startup_seed_fills_empty_db(monkeypatch):
    async def fake_refresh(limit_per_source=50):
        db.upsert_job({"title": "Seed", "source": "s", "external_id": "e", "url": "u"})
        return {"s": 1}

    monkeypatch.setattr(app_module.job_sources, "refresh_jobs", fake_refresh)
    assert db.count_jobs() == 0
    asyncio.run(job_service.startup_seed())
    assert db.count_jobs() == 1
