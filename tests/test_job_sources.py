"""Unit tests: model.job_sources (normalize + refresh + fetcher parsing)."""
import httpx
import pytest

from model import database as db
from model import job_sources


def test_normalize_defaults():
    j = job_sources.normalize("s", {"title": "Dev"})
    assert j["source"] == "s" and j["title"] == "Dev"
    assert j["tags"] == [] and j["company"] == ""


def test_normalize_string_tags():
    j = job_sources.normalize("s", {"title": "Dev", "tags": "a, b"})
    assert j["tags"] == ["a", "b"]


def test_strip_html():
    assert job_sources.strip_html("<p>Hello &amp; <b>world</b></p>") == "Hello & world"
    assert job_sources.strip_html("") == ""
    assert job_sources.strip_html(None) == ""


async def _run(coro):
    return await coro


def test_remotive_parsing():
    payload = {"jobs": [{
        "id": 1, "title": "Remote Dev", "company_name": "R",
        "candidate_required_location": "Worldwide", "job_type": "contract",
        "salary": "$10", "description": "desc", "url": "https://r/1",
        "category": "dev", "publication_date": "2026-01-01",
    }]}

    def handler(request):
        return httpx.Response(200, json=payload)

    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await job_sources.fetch_remotive(client, limit=5)

    jobs = __import__("asyncio").run(go())
    assert len(jobs) >= 1
    assert jobs[0]["source"] == "remotive"
    assert jobs[0]["location"] == "Worldwide"


def test_remotive_rotates_categories():
    seen = []

    def handler(request):
        seen.append(request.url.params.get("category", ""))
        return httpx.Response(200, json={"jobs": []})

    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await job_sources.fetch_remotive(client, limit=10)

    assert __import__("asyncio").run(go()) == []
    assert "" in seen  # baseline without filter
    assert len({c for c in seen if c}) >= 3  # several categories covered


def test_muse_baseline_plus_categories():
    seen = []

    def handler(request):
        seen.append((request.url.params.get("page", "0"),
                     request.url.params.get("category", "")))
        page = request.url.params.get("page", "0")
        return httpx.Response(
            200, json={"results": []} if page != "0" else {"results": [{
                "id": "m1", "name": "Engineer",
                "company": {"name": "Muse Co"}, "locations": [], "levels": [],
                "refs": {}, "contents": "x", "publication_date": "2026-01-03",
                "categories": []}]})

    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await job_sources.fetch_muse(client, limit=10)

    jobs = __import__("asyncio").run(go())
    assert len(jobs) >= 1
    assert any(cat for _, cat in seen)  # at least one category pass ran


def test_fetcher_failure_returns_empty():
    def handler(request):
        raise httpx.ConnectError("down")

    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            assert await job_sources.fetch_remotive(client) == []
            assert await job_sources.fetch_arbeitnow(client) == []
            assert await job_sources.fetch_remoteok(client) == []
            assert await job_sources.fetch_jobicy(client) == []
            assert await job_sources.fetch_muse(client) == []

    __import__("asyncio").run(go())


def test_remoteok_parsing_skips_legal_notice():
    payload = [
        {"legal": "link back to Remote OK"},
        {"id": "9", "slug": "s", "position": "Dev", "company": "C",
         "location": "", "date": "2026-01-01", "url": "https://remoteok.com/x",
         "tags": ["dev"], "description": "<p>hi</p>",
         "salary_min": "100", "salary_max": "200"},
    ]

    def handler(request):
        return httpx.Response(200, json=payload)

    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await job_sources.fetch_remoteok(client)

    jobs = __import__("asyncio").run(go())
    assert len(jobs) >= 1
    assert jobs[0]["source"] == "remoteok"
    assert jobs[0]["location"] == "Remote"  # default when blank
    assert jobs[0]["description"] == "hi"  # html stripped
    assert "$100" in jobs[0]["salary"]


def test_jobicy_parsing():
    payload = {"jobs": [{
        "id": 1, "url": "https://jobicy.com/jobs/1-x", "jobSlug": "1-x",
        "jobTitle": "Designer", "companyName": "D", "jobIndustry": ["Design"],
        "jobType": ["Contract"], "jobGeo": "Germany", "jobLevel": "Senior",
        "jobExcerpt": "excerpt", "jobDescription": "<p>full</p>", "pubDate": "2026-01-02",
    }]}

    def handler(request):
        return httpx.Response(200, json=payload)

    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await job_sources.fetch_jobicy(client)

    jobs = __import__("asyncio").run(go())
    assert len(jobs) >= 1
    assert jobs[0]["type"] == "Contract"
    assert jobs[0]["posted_at"] == "2026-01-02"


def test_muse_parsing():
    payload = {"results": [{
        "id": "m1", "name": "Engineer",
        "company": {"name": "Muse Co"},
        "locations": [{"name": "NYC"}], "levels": [{"name": "Senior"}],
        "refs": {"landing_page": "https://themuse.com/jobs/m1"},
        "contents": "<p>do things</p>", "publication_date": "2026-01-03",
        "categories": [{"name": "Engineering"}],
    }]}

    def handler(request):
        page = request.url.params.get("page", "0")
        return httpx.Response(200, json=payload if page == "0" else {"results": []})

    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await job_sources.fetch_muse(client, limit=10)

    jobs = __import__("asyncio").run(go())
    assert len(jobs) >= 1
    assert jobs[0]["company"] == "Muse Co"
    assert jobs[0]["url"] == "https://themuse.com/jobs/m1"


def test_refresh_upserts_with_mocked_fetchers(monkeypatch):
    async def fake_remotive(client, limit=50):
        return [job_sources.normalize("remotive", {
            "external_id": "r1", "title": "Remote AI", "company": "R",
            "url": "https://r/1"})]

    async def fake_rest(client, limit=50):
        return []

    monkeypatch.setitem(job_sources.FETCHERS, "remotive", fake_remotive)
    for key in ("arbeitnow", "remoteok", "jobicy", "muse",
                "adzuna", "google_jobs", "linkedin", "facebook"):
        monkeypatch.setitem(job_sources.FETCHERS, key, fake_rest)

    counts = __import__("asyncio").run(job_sources.refresh_jobs())
    assert counts["remotive"] == 1
    assert db.count_jobs() == 1
    # second refresh = update, not duplicate
    __import__("asyncio").run(job_sources.refresh_jobs())
    assert db.count_jobs() == 1


def test_linkedin_facebook_slots_are_safe():
    async def go():
        async with httpx.AsyncClient() as client:
            assert await job_sources.fetch_linkedin(client) == []
            assert await job_sources.fetch_facebook(client) == []

    __import__("asyncio").run(go())
