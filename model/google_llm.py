"""Google Gemini provider for JSON analysis (stdlib + httpx only).

Enabled with:
  LLM_PROVIDER=google (or gemini)
  GOOGLE_API_KEY=...
  GEMINI_MODEL=gemini-2.5-flash   (optional; fallback chain covers the rest)

Uses response_mime_type=application/json so the model returns parseable
JSON, matching the local llama.cpp JSON-mode contract: generate_json()
returns the raw JSON text (str) and raises RuntimeError on any failure,
so callers can fall back or retry.

Model-name reality (Oct 2026): Google shuts down old Flash models regularly
(2.0-flash -> 404 since Jun 2026) and new keys may lack access to some 2.5
models. So a primary 404 automatically falls through FALLBACK_MODELS.
Transient errors (429/5xx, network) get one retry per model.

Safety rules (the API key must never leak into logs/errors):
  - every raised message passes through _redact() (key=REDACTED).
"""
import os
import re
import time

import httpx

TIMEOUT = 120.0
RETRIES_PER_MODEL = 1
BACKOFF = 3.0

FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-3.5-flash",
                   "gemini-3.6-flash", "gemini-3.1-flash-lite"]

# Last model that actually answered (surfaced in /admin/stats).
last_model = None


def _redact(text):
    """Replace key=<secret> with key=REDACTED in any message/URL."""
    return re.sub(r"(key=)[^&\s'\"]+", r"\1REDACTED", str(text))


def _status_of(exc):
    resp = getattr(exc, "response", None)
    return getattr(resp, "status_code", None)


def _candidate_models():
    primary = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() \
        or "gemini-2.5-flash"
    seen, out = set(), []
    for m in [primary] + FALLBACK_MODELS:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def _post_once(url, api_key, payload):
    resp = httpx.post(url, params={"key": api_key}, json=payload,
                      timeout=TIMEOUT)
    resp.raise_for_status()
    try:
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError, ValueError) as e:
        raise RuntimeError(f"Unexpected Gemini response shape: {e}")


def generate_json(system, user, max_tokens=1500):
    global last_model
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set (LLM_PROVIDER=google needs it)")
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"parts": [{"text": user}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.0,
            "maxOutputTokens": max_tokens,
        },
    }
    last_error = None
    for model in _candidate_models():
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{model}:generateContent")
        for attempt in range(RETRIES_PER_MODEL + 1):
            try:
                text = _post_once(url, api_key, payload)
                last_model = model
                return text
            except RuntimeError:
                raise  # malformed response shape — retrying won't help
            except Exception as e:
                status = _status_of(e) if isinstance(
                    e, httpx.HTTPStatusError) else None
                if status in (400, 401, 403, 404):
                    last_error = (
                        f"Model {model} refused (HTTP {status}): "
                        f"unknown model name or bad key. Detail: {_redact(e)}")
                    break  # next model in chain
                last_error = e
                if attempt < RETRIES_PER_MODEL:
                    time.sleep(BACKOFF)
                    continue
                last_error = (
                    f"Model {model} failed after "
                    f"{RETRIES_PER_MODEL + 1} tries: {_redact(e)}")
                break  # next model in chain
    raise RuntimeError(
        f"Gemini request failed (tried: {', '.join(_candidate_models())}). "
        f"Last error: {_redact(last_error)}")
