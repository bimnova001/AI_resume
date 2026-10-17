"""Unit tests: model.jsonutil + model.rule + model.parser."""
import fitz
import pytest

from model.jsonutil import parse_llm_json
from model.parser import PDFExtractError, extract_pdf
from model.rule import analyze_resume_structure


# ---------- jsonutil ----------

def test_parse_plain_json():
    assert parse_llm_json('{"a": 1}') == {"a": 1}


def test_parse_noisy_llm_output():
    raw = 'Here you go: {"resume_score": 80, "summary": "good",} bye'
    assert parse_llm_json(raw) == {"resume_score": 80, "summary": "good"}


def test_parse_invalid_returns_none():
    assert parse_llm_json("no json here") is None
    assert parse_llm_json("") is None
    assert parse_llm_json(None) is None
    assert parse_llm_json(123) is None


def test_parse_strips_markdown_fences():
    assert parse_llm_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_llm_json('```\n{"a": 2}\n```') == {"a": 2}
    assert parse_llm_json('Here:\n```json\n{"a": 3,}\n```') == {"a": 3}


def test_parse_truncated_json_returns_none():
    assert parse_llm_json('{"a": 1, "b": [2,') is None


# ---------- rule ----------

def test_rule_empty_text():
    r = analyze_resume_structure("")
    assert r["education"] is False
    assert r["details"]["error"] == "empty text"


def test_rule_detects_all_sections():
    text = """
    Education: B.Sc Computer Science
    Skills: Python, Docker
    Projects: RAG chatbot
    Experience: Intern at AI Labs
    github.com/example
    Portfolio: https://example.dev
    """
    r = analyze_resume_structure(text)
    assert r["education"] and r["skills"] and r["projects"]
    assert r["experience"] and r["github"] and r["portfolio"]


def test_rule_no_substring_false_positive():
    r = analyze_resume_structure("I am a skilled worker with no sections.")
    assert r["skills"] is False


def test_rule_thai_headings():
    r = analyze_resume_structure("การศึกษา: ปริญญาตรี\nทักษะ: Python\nประสบการณ์ทำงาน: 2 ปี")
    assert r["education"] is True
    assert r["skills"] is True
    assert r["experience"] is True


def test_rule_contact_details():
    r = analyze_resume_structure("Contact me@example.com or +66 81 234 5678, see linkedin.com/in/me")
    assert r["details"]["contact_email"] == "me@example.com"
    assert r["details"]["linkedin"] is not None


# ---------- parser ----------

def _make_pdf(path, text):
    doc = fitz.open()
    page = doc.new_page()
    if text:
        page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def test_parser_extracts_text(tmp_path):
    pdf = tmp_path / "resume.pdf"
    _make_pdf(str(pdf), "Hello AI Engineer")
    assert "Hello AI Engineer" in extract_pdf(str(pdf))


def test_parser_missing_file():
    with pytest.raises(PDFExtractError):
        extract_pdf("does-not-exist.pdf")


def test_parser_empty_pdf_rejected(tmp_path):
    pdf = tmp_path / "blank.pdf"
    _make_pdf(str(pdf), "")
    with pytest.raises(PDFExtractError):
        extract_pdf(str(pdf))


def test_parser_non_pdf_rejected(tmp_path):
    txt = tmp_path / "note.txt"
    txt.write_text("just text", encoding="utf-8")
    with pytest.raises(PDFExtractError):
        extract_pdf(str(txt))
