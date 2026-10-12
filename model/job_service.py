"""Background job-fetching service.

The SERVER pulls postings by itself — users never have to press refresh:
  - seed once on startup when the DB is empty,
  - re-fetch every JOBS_REFRESH_HOURS (default 6) via a scheduler task,
  - manual POST /jobs/refresh just triggers the same pipeline early.

State (last run, per-source counts) lives in the DB meta table so any
worker/process sees the same status. A module-level flag guards against
overlapping runs within one process.
"""
import asyncio
import json
import os
from datetime import datetime, timezone

from model import database as db
from model import job_sources
from logger import logger

_running = False
_scheduler_task = None


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def is_refreshing():
    return _running


async def refresh_now(limit_per_source=30):
    """Run one fetch cycle. Returns a status dict (never raises)."""
    global _running
    if _running:
        return {"status": "already_running", **get_status()}
    _running = True
    try:
        counts = await job_sources.refresh_jobs(limit_per_source=limit_per_source)
        total = db.count_jobs()
        db.set_meta("jobs_last_refresh", _now_iso())
        db.set_meta("jobs_last_counts", json.dumps(counts, ensure_ascii=False))
        db.set_meta("jobs_last_total", str(total))
        db.write_log("jobs_refresh", json.dumps(counts, ensure_ascii=False))
        logger.info(f"Jobs refresh done: {counts} (total {total})")
        return {"status": "success", "counts": counts, "total": total}
    except Exception as e:
        logger.error(f"Jobs refresh failed: {e}")
        return {"status": "error", "error": str(e), **get_status()}
    finally:
        _running = False


def get_status():
    try:
        total = db.count_jobs()
    except Exception:
        total = 0
    try:
        counts = json.loads(db.get_meta("jobs_last_counts") or "{}")
    except (json.JSONDecodeError, TypeError):
        counts = {}
    return {
        "total": total,
        "refreshing": _running,
        "last_refresh_at": db.get_meta("jobs_last_refresh") or None,
        "last_counts": counts,
        "auto_refresh": os.getenv("JOBS_AUTO_REFRESH", "1") == "1",
        "interval_hours": float(os.getenv("JOBS_REFRESH_HOURS", "6") or 6),
    }


def _last_refresh_ts():
    raw = db.get_meta("jobs_last_refresh")
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except ValueError:
        return None


async def scheduler_loop():
    """Sleep until the next due time, then refresh. Cancel-safe."""
    while True:
        try:
            interval = float(os.getenv("JOBS_REFRESH_HOURS", "6") or 6) * 3600
            last = _last_refresh_ts()
            if last is None:
                wait = 60.0  # never refreshed: retry soon
            else:
                import time
                wait = max(60.0, last + interval - time.time())
            await asyncio.sleep(wait)
            if os.getenv("JOBS_AUTO_REFRESH", "1") != "1":
                continue
            if not _running:
                await refresh_now(limit_per_source=30)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning(f"Jobs scheduler error: {e}")
            await asyncio.sleep(300)


async def startup_seed():
    """Fetch once at boot when the DB has no postings yet."""
    try:
        if db.count_jobs() == 0:
            logger.info("Jobs DB empty, seeding real postings in background")
            await refresh_now(limit_per_source=50)
    except Exception as e:
        logger.warning(f"Jobs seed failed: {e}")


def start_scheduler():
    global _scheduler_task
    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = asyncio.create_task(scheduler_loop())
    return _scheduler_task


async def stop_scheduler():
    global _scheduler_task
    if _scheduler_task is not None:
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
        _scheduler_task = None
