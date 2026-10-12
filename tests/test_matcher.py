"""Unit tests: model.matcher (keywords + ranking, embedding injected)."""
from model import database as db
from model import matcher


def _seed():
    db.upsert_job({"title": "Python Backend Developer", "company": "PyCo",
                   "description": "Python, Docker, PostgreSQL everyday",
                   "source": "t", "external_id": "py1", "url": "u1",
                   "tags": ["Python", "Docker"]})
    db.upsert_job({"title": "UX Designer", "company": "DesignCo",
                   "description": "Figma, user research, prototypes",
                   "source": "t", "external_id": "ux1", "url": "u2"})


def test_extract_keywords():
    kws = matcher.extract_keywords(
        "Python developer with Docker and Python experience. Team player, responsible role.")
    assert "python" in kws and "docker" in kws
    assert "team" not in kws and "the" not in kws  # stopwords


def test_extract_keywords_empty():
    assert matcher.extract_keywords("") == []
    assert matcher.extract_keywords(None) == []


def test_suggest_ranks_relevant_first():
    _seed()
    resume = "Python developer, Docker containers, PostgreSQL databases"

    def fake_sim(r, jt):
        jt = jt.lower()
        return 95.0 if "python" in jt else 10.0

    out = matcher.suggest_jobs(resume, limit=3, similarity_fn=fake_sim)
    assert len(out) == 1  # pre-filter drops the unrelated UX job
    assert out[0]["title"] == "Python Backend Developer"
    assert out[0]["match"] == 95.0
    assert "python" in out[0]["matched_skills"]
    assert out[0]["reason"].startswith("Match 95.0%")
    assert {"id", "title", "company", "url", "source", "posted_at"} <= set(out[0])

    ux = matcher.suggest_jobs("Figma designer, user research prototypes",
                              limit=3, similarity_fn=fake_sim)
    assert [j["title"] for j in ux] == ["UX Designer"]


def test_suggest_limit():
    _seed()
    out = matcher.suggest_jobs("Python Docker", limit=1,
                               similarity_fn=lambda r, j: 50.0)
    assert len(out) == 1


def test_suggest_empty_db_or_text():
    assert matcher.suggest_jobs("Python developer",
                                similarity_fn=lambda r, j: 90.0) == []
    _seed()
    assert matcher.suggest_jobs("", similarity_fn=lambda r, j: 90.0) == []
    assert matcher.suggest_jobs("   ", similarity_fn=lambda r, j: 90.0) == []


def test_suggest_never_raises():
    _seed()

    def boom(r, j):
        raise RuntimeError("model down")

    assert matcher.suggest_jobs("Python", similarity_fn=boom) == []
