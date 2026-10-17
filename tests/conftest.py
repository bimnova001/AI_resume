"""Pytest bootstrap: isolate SQLite per test session run."""
import os
import tempfile

_tmpdir = tempfile.mkdtemp(prefix="ai_resume_tests_")
os.environ["DB_PATH"] = os.path.join(_tmpdir, "test.db")
os.environ["JOBS_AUTO_SEED"] = "0"
os.environ["JOBS_AUTO_REFRESH"] = "0"
# Hermetic LLM config: the dev machine's .env may point at a real provider
# (loaded via load_dotenv on `import app`). Tests must never touch it.
os.environ["LLM_PROVIDER"] = "local"
os.environ.pop("GOOGLE_API_KEY", None)
os.environ.pop("GEMINI_MODEL", None)

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
