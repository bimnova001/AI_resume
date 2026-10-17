"""Lightweight JSON parsing for noisy LLM output. No heavy dependencies."""
import json
import re


def _strip_fences(text):
    """Remove ```json ... ``` / ``` ... ``` wrappers models love to add."""
    t = text.strip()
    if t.startswith("```"):
        lines = t.split("\n")
        lines = lines[1:]  # drop opening fence (``` or ```json)
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]  # drop closing fence
        t = "\n".join(lines).strip()
    return t


def parse_llm_json(text):
    """Parse (possibly truncated/noisy) LLM output as JSON. Single source of truth."""
    if not isinstance(text, str):
        return None
    text = _strip_fences(text.strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        if start == -1:
            return None
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start:i + 1]
                    candidate = re.sub(r",\s*}", "}", candidate)
                    candidate = re.sub(r",\s*]", "]", candidate)
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        return None
                    break
        return None
