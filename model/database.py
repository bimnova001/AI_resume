"""SQLite storage (stdlib only): jobs cache, users/sessions, history, logs.

Designed to grow: add tables/columns here, endpoints in app.py stay thin.
DB path: env DB_PATH (default ./data/app.db).
"""
import hashlib
import json
import os
import secrets
import sqlite3
import threading
from datetime import datetime, timezone

_lock = threading.Lock()


def db_path():
    return os.getenv("DB_PATH", os.path.join("data", "app.db"))


def _connect():
    path = db_path()
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT 'manual',
    title TEXT NOT NULL,
    company TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT '',
    type TEXT NOT NULL DEFAULT '',
    salary TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '[]',
    posted_at TEXT NOT NULL DEFAULT '',
    fetched_at TEXT NOT NULL DEFAULT '',
    UNIQUE(source, external_id)
);
CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    pw_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analysis_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    job_title TEXT NOT NULL,
    job_type TEXT NOT NULL DEFAULT '',
    job_match REAL,
    resume_score REAL,
    language TEXT NOT NULL DEFAULT 'en',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_history_user ON analysis_history(user_id);

CREATE TABLE IF NOT EXISTS saved_jobs (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    PRIMARY KEY (user_id, job_id)
);

CREATE TABLE IF NOT EXISTS app_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL DEFAULT 'INFO',
    event TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT '',
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL
);
"""


def init_db():
    with _lock:
        conn = _connect()
        try:
            conn.executescript(SCHEMA)
            conn.commit()
        finally:
            conn.close()


def _now():
    return datetime.now(timezone.utc).isoformat()


# ---------------- jobs ----------------

JOB_FIELDS = (
    "external_id", "source", "title", "company", "location", "type",
    "salary", "description", "url", "tags", "posted_at",
)


def upsert_job(job):
    """Insert or update a job keyed by (source, external_id). Returns row id."""
    tags = job.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    row = {
        "external_id": str(job.get("external_id", job.get("url", ""))),
        "source": str(job.get("source", "manual")),
        "title": str(job.get("title", "")),
        "company": str(job.get("company", "")),
        "location": str(job.get("location", "")),
        "type": str(job.get("type", "")),
        "salary": str(job.get("salary", "")),
        "description": str(job.get("description", "")),
        "url": str(job.get("url", "")),
        "tags": json.dumps(list(tags), ensure_ascii=False),
        "posted_at": str(job.get("posted_at", "")),
    }
    if not row["title"]:
        raise ValueError("job title is required")
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                """INSERT INTO jobs (external_id, source, title, company, location,
                                     type, salary, description, url, tags, posted_at, fetched_at)
                   VALUES (:external_id, :source, :title, :company, :location,
                           :type, :salary, :description, :url, :tags, :posted_at, :fetched_at)
                   ON CONFLICT(source, external_id) DO UPDATE SET
                     title=excluded.title, company=excluded.company,
                     location=excluded.location, type=excluded.type,
                     salary=excluded.salary, description=excluded.description,
                     url=excluded.url, tags=excluded.tags,
                     posted_at=excluded.posted_at, fetched_at=excluded.fetched_at""",
                {**row, "fetched_at": _now()},
            )
            conn.commit()
            cur = conn.execute(
                "SELECT id FROM jobs WHERE source=? AND external_id=?",
                (row["source"], row["external_id"]),
            )
            return cur.fetchone()["id"]
        finally:
            conn.close()


def _job_to_dict(r):
    d = dict(r)
    try:
        d["tags"] = json.loads(d.get("tags") or "[]")
    except (json.JSONDecodeError, TypeError):
        d["tags"] = []
    return d


def list_jobs(q="", location="", source="", job_type="", limit=50, offset=0):
    limit = max(1, min(int(limit or 50), 200))
    offset = max(0, int(offset or 0))
    conds, params = [], []
    if q:
        conds.append("(title LIKE ? OR company LIKE ? OR description LIKE ?)")
        like = f"%{q}%"
        params += [like, like, like]
    if location:
        conds.append("location LIKE ?")
        params.append(f"%{location}%")
    if source:
        conds.append("source = ?")
        params.append(source)
    if job_type:
        conds.append("type LIKE ?")
        params.append(f"%{job_type}%")
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    with _lock:
        conn = _connect()
        try:
            total = conn.execute(f"SELECT COUNT(*) c FROM jobs {where}", params).fetchone()["c"]
            rows = conn.execute(
                f"SELECT * FROM jobs {where} ORDER BY id DESC LIMIT ? OFFSET ?",
                (*params, limit, offset),
            ).fetchall()
            return {"total": total, "jobs": [_job_to_dict(r) for r in rows]}
        finally:
            conn.close()


def get_job(job_id):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            return _job_to_dict(row) if row else None
        finally:
            conn.close()


def count_jobs():
    with _lock:
        conn = _connect()
        try:
            return conn.execute("SELECT COUNT(*) c FROM jobs").fetchone()["c"]
        finally:
            conn.close()


# ---------------- users / sessions ----------------

def _hash_password(password, salt_hex):
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 200_000
    ).hex()


def create_user(name, email, password):
    name = (name or "").strip()
    email = (email or "").strip().lower()
    if not name or not email or "@" not in email:
        raise ValueError("name and valid email are required")
    if not password or len(password) < 8:
        raise ValueError("password must be at least 8 characters")
    salt = secrets.token_hex(16)
    with _lock:
        conn = _connect()
        try:
            try:
                cur = conn.execute(
                    "INSERT INTO users (name, email, pw_hash, salt, created_at)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (name, email, _hash_password(password, salt), salt, _now()),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                raise ValueError("email already registered")
            return {"id": cur.lastrowid, "name": name, "email": email}
        finally:
            conn.close()


def verify_user(email, password):
    email = (email or "").strip().lower()
    with _lock:
        conn = _connect()
        try:
            row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            if not row:
                return None
            if _hash_password(password or "", row["salt"]) != row["pw_hash"]:
                return None
            return {"id": row["id"], "name": row["name"], "email": row["email"]}
        finally:
            conn.close()


def create_session(user_id):
    token = secrets.token_urlsafe(32)
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
                (token, user_id, _now()),
            )
            conn.commit()
            return token
        finally:
            conn.close()


def get_user_by_token(token):
    if not token:
        return None
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT u.id, u.name, u.email FROM sessions s"
                " JOIN users u ON u.id = s.user_id WHERE s.token=?",
                (token,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()


def delete_session(token):
    with _lock:
        conn = _connect()
        try:
            conn.execute("DELETE FROM sessions WHERE token=?", (token,))
            conn.commit()
        finally:
            conn.close()


# ---------------- history / saved / logs ----------------

def save_analysis(user_id, job_title, job_type="", job_match=None, resume_score=None, language="en"):
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute(
                """INSERT INTO analysis_history
                   (user_id, job_title, job_type, job_match, resume_score, language, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, job_title, job_type, job_match, resume_score, language, _now()),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()


def list_history(user_id, limit=50, offset=0):
    if user_id is None:
        return []
    limit = max(1, min(int(limit or 50), 200))
    offset = max(0, int(offset or 0))
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT * FROM analysis_history WHERE user_id = ?"
                " ORDER BY id DESC LIMIT ? OFFSET ?",
                (user_id, limit, offset),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


def save_job_for_user(user_id, job_id):
    with _lock:
        conn = _connect()
        try:
            if not conn.execute("SELECT id FROM jobs WHERE id=?", (job_id,)).fetchone():
                raise ValueError("job not found")
            conn.execute(
                "INSERT OR IGNORE INTO saved_jobs (user_id, job_id, created_at)"
                " VALUES (?, ?, ?)",
                (user_id, job_id, _now()),
            )
            conn.commit()
        finally:
            conn.close()


def list_saved_jobs(user_id):
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT j.* FROM saved_jobs s JOIN jobs j ON j.id = s.job_id"
                " WHERE s.user_id = ? ORDER BY s.created_at DESC",
                (user_id,),
            ).fetchall()
            return [_job_to_dict(r) for r in rows]
        finally:
            conn.close()


def write_log(event, detail="", level="INFO", user_id=None):
    try:
        with _lock:
            conn = _connect()
            try:
                conn.execute(
                    "INSERT INTO app_logs (level, event, detail, user_id, created_at)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (level, event, detail, user_id, _now()),
                )
                conn.commit()
            finally:
                conn.close()
    except Exception:
        pass


# ---------------- key/value meta (service state) ----------------

def set_meta(key, value):
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO meta (key, value, updated_at) VALUES (?, ?, ?)"
                " ON CONFLICT(key) DO UPDATE SET value=excluded.value,"
                " updated_at=excluded.updated_at",
                (key, str(value), _now()),
            )
            conn.commit()
        finally:
            conn.close()


def get_meta(key, default=""):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
            return row["value"] if row else default
        finally:
            conn.close()
