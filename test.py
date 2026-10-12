"""Smoke/demo tests (run with: pytest test.py -v)."""
import json

from model.jsonutil import parse_llm_json
from model.rule import analyze_resume_structure


def test_parse_llm_json_plain():
    assert parse_llm_json('{"a": 1}') == {"a": 1}


def test_parse_llm_json_noisy():
    raw = 'Here is the result: {"resume_score": 80, "summary": "good",} done'
    assert parse_llm_json(raw) == {"resume_score": 80, "summary": "good"}


def test_parse_llm_json_invalid():
    assert parse_llm_json("no json here") is None
    assert parse_llm_json(None) is None


def test_rule_empty_text():
    result = analyze_resume_structure("")
    assert result["education"] is False


def test_rule_detects_sections():
    text = """
    Education: B.Sc Computer Science
    Skills: Python, Docker
    Projects: RAG chatbot
    Experience: Intern at AI Labs
    github.com/example
    Portfolio: https://example.dev
    Contact: me@example.com +66 81 234 5678
    """
    result = analyze_resume_structure(text)
    assert result["education"] is True
    assert result["skills"] is True
    assert result["projects"] is True
    assert result["experience"] is True
    assert result["github"] is True
    assert result["portfolio"] is True


def test_rule_avoids_substring_false_positive():
    # "skilled" alone should not count as a Skills section
    result = analyze_resume_structure("I am a skilled worker with no sections.")
    assert result["skills"] is False
