"""Unit tests: model.llm (fully mocked — never downloads/loads a model)."""
import json

import model.llm as llm_mod
from model import llm as llm


class FakeLlama:
    """Canned create_chat_completion returning queued replies + recording calls."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def create_chat_completion(self, **kwargs):
        self.calls.append(kwargs)
        text = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        return {"choices": [{"message": {"content": text}}]}


def _patch(monkeypatch, replies):
    fake = FakeLlama(replies)
    monkeypatch.setattr(llm_mod, "get_llm", lambda: fake)
    return fake


def test_analyze_returns_valid_json_first_try(monkeypatch):
    payload = {"resume_score": 80, "summary": "good", "strengths": [],
               "weaknesses": [], "missing_skills": [],
               "recommended_projects": [], "recommended_certificates": [],
               "career_paths": [], "recommended_actions": [], "match_comment": "ok"}
    fake = _patch(monkeypatch, [json.dumps(payload)])
    out = llm.analyze_resume("Python dev resume", "AI Engineer", 78.5,
                             {"skills": True}, "ml", False, "en")
    assert json.loads(out)["resume_score"] == 80
    assert len(fake.calls) == 1  # no repair needed
    call = fake.calls[0]
    assert call["response_format"] == {"type": "json_object"}
    assert call["temperature"] == 0.0


def test_analyze_repairs_invalid_json(monkeypatch):
    good = '{"resume_score": 70, "summary": "fixed"}'
    fake = _patch(monkeypatch, ["oops not json", good])
    out = llm.analyze_resume("resume", "Dev", 50, {}, "", True, "en")
    assert json.loads(out)["summary"] == "fixed"
    assert len(fake.calls) == 2  # original + repair


def test_analyze_gives_up_gracefully(monkeypatch):
    fake = _patch(monkeypatch, ["garbage{{"])
    out = llm.analyze_resume("resume", "Dev", 50, {}, "", False, "en")
    assert out == "garbage{{"  # caller falls back to raw text
    assert len(fake.calls) == 2


def test_analyze_thai_values(monkeypatch):
    fake = _patch(monkeypatch, ['{"resume_score": 1, "summary": "x"}'])
    llm.analyze_resume("resume", "Dev", 50, {}, "", False, "th")
    system = fake.calls[0]["messages"][0]["content"]
    assert "Thai" in system


def test_market_analysis_json_mode(monkeypatch):
    payload = {"top_emerging_technologies": ["RAG"], "popular_tools": [],
               "ai_engineer_relevant": [], "student_relevant": [],
               "recommended_skills": [], "market_summary": "s"}
    fake = _patch(monkeypatch, [json.dumps(payload)])
    out = llm.Market_Analysis('{"hacker_news": []}')
    assert json.loads(out)["top_emerging_technologies"] == ["RAG"]
    assert fake.calls[0]["response_format"] == {"type": "json_object"}


def test_default_model_is_7b():
    assert "7B" in llm_mod.DEFAULT_REPO or "7b" in llm_mod.DEFAULT_FILE
    assert "3B" not in llm_mod.DEFAULT_REPO and "3b" not in llm_mod.DEFAULT_FILE
