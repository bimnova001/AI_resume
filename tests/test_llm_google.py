"""Unit tests: Google Gemini provider + LLM provider switch (no network)."""
import httpx
import pytest

import model.llm as llm_mod
from model import google_llm, llm


class _Resp:
    def __init__(self, payload=None, error=None):
        self._payload = payload
        self._error = error

    def raise_for_status(self):
        if self._error:
            raise self._error

    def json(self):
        return self._payload


def _gemini_payload(text):
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


def test_generate_json_success(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "k")
    monkeypatch.setattr(httpx, "post",
                        lambda *a, **k: _Resp(_gemini_payload('{"a": 1}')))
    assert google_llm.generate_json("sys", "user") == '{"a": 1}'


def test_generate_json_uses_configured_model(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "k")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-x-test")
    seen = {}

    def fake_post(url, **kwargs):
        seen["url"] = url
        return _Resp(_gemini_payload("{}"))

    monkeypatch.setattr(httpx, "post", fake_post)
    google_llm.generate_json("sys", "user")
    assert "gemini-x-test" in seen["url"]


def test_generate_json_missing_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
        google_llm.generate_json("sys", "user")


def test_generate_json_bad_shape(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "k")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _Resp({"nope": 1}))
    with pytest.raises(RuntimeError, match="Unexpected Gemini"):
        google_llm.generate_json("sys", "user")


def test_generate_json_http_error(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "k")
    monkeypatch.setattr("model.google_llm.time.sleep", lambda s: None)

    def boom(*a, **k):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(httpx, "post", boom)
    with pytest.raises(RuntimeError, match="Gemini request failed"):
        google_llm.generate_json("sys", "user")


def _status_error(status):
    # Same shape as real httpx errors: message embeds the full URL incl. key.
    url = "https://x.test/m?key=SECRET123"
    req = httpx.Request("POST", url)
    msg = f"Server error '{status}' for url '{url}'"
    return httpx.HTTPStatusError(msg, request=req,
                                 response=httpx.Response(status, request=req))


def test_generate_json_retries_transient_then_succeeds(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "k")
    monkeypatch.setattr("model.google_llm.time.sleep", lambda s: None)
    calls = []

    def flaky(*a, **k):
        calls.append(1)
        if len(calls) == 1:
            raise _status_error(503)
        return _Resp(_gemini_payload('{"ok": true}'))

    monkeypatch.setattr(httpx, "post", flaky)
    assert google_llm.generate_json("sys", "user") == '{"ok": true}'
    assert len(calls) == 2


def test_generate_json_404_falls_through_chain(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "k")
    monkeypatch.setenv("GEMINI_MODEL", "bad-model")
    monkeypatch.setattr("model.google_llm.time.sleep", lambda s: None)
    monkeypatch.setattr(google_llm, "FALLBACK_MODELS", ["good-model"])
    calls = []

    def router(*a, **k):
        import re as _re
        m = _re.search(r"models/([^:]+):", a[0])
        calls.append(m.group(1))
        if m.group(1) == "bad-model":
            raise _status_error(404)
        return _Resp(_gemini_payload('{"ok": true}'))

    monkeypatch.setattr(httpx, "post", router)
    assert google_llm.generate_json("sys", "user") == '{"ok": true}'
    assert calls == ["bad-model", "good-model"]
    assert google_llm.last_model == "good-model"


def test_generate_json_all_models_fail(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "k")
    monkeypatch.setenv("GEMINI_MODEL", "m1")
    monkeypatch.setattr("model.google_llm.time.sleep", lambda s: None)
    monkeypatch.setattr(google_llm, "FALLBACK_MODELS", ["m2"])
    monkeypatch.setattr(httpx, "post",
                        lambda *a, **k: (_ for _ in ()).throw(_status_error(404)))
    with pytest.raises(RuntimeError, match="tried: m1, m2"):
        google_llm.generate_json("sys", "user")


def test_api_key_never_leaks_into_errors(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "SUPERSECRET")
    monkeypatch.setattr("model.google_llm.time.sleep", lambda s: None)
    monkeypatch.setattr(httpx, "post",
                        lambda *a, **k: (_ for _ in ()).throw(_status_error(503)))
    try:
        google_llm.generate_json("sys", "user")
        raise AssertionError("should have raised")
    except RuntimeError as e:
        assert "SUPERSECRET" not in str(e)
        assert "REDACTED" in str(e)


def test_provider_google_dispatch(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "google")
    calls = {}

    def fake_generate(system, user, max_tokens=1500):
        calls["system"] = system
        return '{"resume_score": 9, "summary": "g"}'

    monkeypatch.setattr("model.google_llm.generate_json", fake_generate)
    out = llm.analyze_resume("resume", "Dev", 10, {}, "", False, "en")
    assert '"resume_score": 9' in out
    assert "HR expert" in calls["system"]


def test_provider_google_falls_back_to_cached_local(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "google")

    def always_fail(system, user, max_tokens=1500):
        raise RuntimeError("Gemini request failed after 3 tries (model=x)")

    class FakeLocal:
        def create_chat_completion(self, **kw):
            return {"choices": [{"message": {"content": '{"resume_score": 5}'}}]}

    monkeypatch.setattr("model.google_llm.generate_json", always_fail)
    monkeypatch.setattr(llm_mod, "_local_model_cached", lambda: True)
    monkeypatch.setattr(llm_mod, "get_llm", lambda: FakeLocal())
    out = llm.analyze_resume("resume", "Dev", 10, {}, "", False, "en")
    assert '"resume_score": 5' in out


def test_provider_google_no_cache_raises(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "google")

    def always_fail(system, user, max_tokens=1500):
        raise RuntimeError("Gemini request failed")

    monkeypatch.setattr("model.google_llm.generate_json", always_fail)
    monkeypatch.setattr(llm_mod, "_local_model_cached", lambda: False)
    with pytest.raises(RuntimeError, match="Gemini request failed"):
        llm.analyze_resume("resume", "Dev", 10, {}, "", False, "en")


def test_provider_default_is_local(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    assert llm_mod._provider() == "local"
