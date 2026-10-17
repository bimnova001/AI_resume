"""Locale integrity: 10 languages, identical key sets, valid JSON."""
import io
import json
import os
import re
import glob

import pytest

BASE = r"D:\Ai_resumee\web\locales"
EXPECTED = ["en", "th", "zh", "ja", "ko", "vi", "id", "ms", "hi", "es"]


def _load(lng):
    p = os.path.join(BASE, lng, "translation.json")
    assert os.path.isfile(p), f"missing locale file: {p}"
    with io.open(p, encoding="utf-8") as f:
        return json.load(f)


def _flat(d, prefix=""):
    out = {}
    for k, v in d.items():
        key = prefix + "." + k if prefix else k
        if isinstance(v, dict):
            out.update(_flat(v, key))
        else:
            out[key] = v
    return out


def test_ten_language_directories_exist():
    found = sorted(os.path.basename(os.path.dirname(p))
                   for p in glob.glob(os.path.join(BASE, "*", "translation.json")))
    assert found == sorted(EXPECTED), found


@pytest.mark.parametrize("lng", EXPECTED)
def test_locale_json_valid(lng):
    d = _load(lng)
    assert isinstance(d, dict) and d


@pytest.mark.parametrize("lng", EXPECTED)
def test_locale_has_all_keys(lng):
    en = _flat(_load("en"))
    cur = _flat(_load(lng))
    missing = sorted(set(en) - set(cur))
    extra = sorted(set(cur) - set(en))
    assert not missing, f"{lng} missing keys: {missing}"
    assert not extra, f"{lng} has unknown keys: {extra}"


@pytest.mark.parametrize("lng", EXPECTED)
def test_locale_values_are_nonempty_strings(lng):
    for k, v in _flat(_load(lng)).items():
        assert isinstance(v, str), f"{lng}:{k} not a string"
        assert v.strip(), f"{lng}:{k} is empty"


def test_nav_and_resume_keys_present():
    for lng in EXPECTED:
        d = _load(lng)
        for sec in ("nav", "resume", "listings", "details", "saved", "market",
                    "login", "admin", "common", "profile"):
            assert sec in d, f"{lng} missing section {sec}"


def test_supported_langs_in_i18n_js_match_directories():
    js = io.open(r"D:\Ai_resumee\web\public\js\i18n.js", encoding="utf-8").read()
    block = js.split("SUPPORTED_LANGS = [")[1].split("];")[0]
    codes = re.findall(r"\['([a-z]{2})'", block)
    assert sorted(codes) == sorted(EXPECTED), codes
