"""Pytest bootstrap: isolate SQLite per test session run."""
import os
import tempfile

_tmpdir = tempfile.mkdtemp(prefix="ai_resume_tests_")
os.environ["DB_PATH"] = os.path.join(_tmpdir, "test.db")
os.environ["JOBS_AUTO_SEED"] = "0"
os.environ["JOBS_AUTO_REFRESH"] = "0"

import pytest  # noqa: E402

from model import database as db  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_db():
    """Wipe all tables before each test for full isolation."""
    db.init_db()
    conn = db._connect()
    try:
        for table in ("saved_jobs", "analysis_history", "sessions",
                      "users", "jobs", "app_logs"):
            conn.execute(f"DELETE FROM {table}")
        conn.commit()
    finally:
        conn.close()
    yield
