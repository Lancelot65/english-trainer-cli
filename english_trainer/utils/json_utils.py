"""JSON parsing utilities."""

import json
from typing import Any, Dict, Optional


def extract_first_json_object(text: str) -> Optional[str]:
    """
    Extract the first JSON object from text, handling code blocks.

    Args:
        text: Text that may contain JSON

    Returns:
        JSON string or None if not found
    """
    if not text:
        return None

    s = text.strip()

    # Handle code blocks (multiple formats)
    if s.startswith("```"):
        lines = s.splitlines()
        # Remove first line (```json or ```)
        if len(lines) > 1:
            lines = lines[1:]
        # Remove last line if it's closing ```
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        s = "\n".join(lines).strip()

    # Handle markdown code blocks
    if s.startswith("`") and s.endswith("`"):
        s = s.strip("`").strip()

    # Try multiple JSON extraction strategies
    def _simple_extraction(x: str) -> Optional[str]:
        if "{" in x and "}" in x:
            return x[x.find("{") : x.rfind("}") + 1]
        return None

    strategies = [
        lambda x: x,  # Direct text
        _simple_extraction,  # Simple extraction
        _extract_balanced_json,  # Balanced bracket extraction
    ]

    for strategy in strategies:
        try:
            candidate = strategy(s)
            if (
                candidate
                and candidate.strip().startswith("{")
                and candidate.strip().endswith("}")
            ):
                return candidate.strip()
        except Exception:
            continue

    return None


def _extract_balanced_json(text: str) -> Optional[str]:
    """Extract JSON using balanced bracket matching."""
    if not text:
        return None

    # Find JSON object boundaries
    start = text.find("{")
    if start < 0:
        return None

    depth = 0
    in_string = False
    escaped = False

    for i in range(start, len(text)):
        char = text[i]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    return None


def parse_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON from text with fallback extraction.

    Args:
        text: Text containing JSON

    Returns:
        Parsed JSON dict or None if parsing fails
    """
    if not text:
        return None

    # Try direct parsing first
    try:
        obj = json.loads(text.strip())
        if isinstance(obj, dict):
            return obj
        return None
    except (json.JSONDecodeError, ValueError):
        pass

    # Try extracting JSON object
    json_block = extract_first_json_object(text)
    if not json_block:
        return None

    try:
        obj = json.loads(json_block)
        if isinstance(obj, dict):
            return obj
        return None
    except (json.JSONDecodeError, ValueError):
        return None


def clamp_int(value: Any, min_val: int, max_val: int, default: int) -> int:
    """
    Clamp integer value to range with default fallback.

    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        default: Default if conversion fails

    Returns:
        Clamped integer value
    """
    try:
        v = int(value)
        return max(min_val, min(max_val, v))
    except (ValueError, TypeError):
        return default
