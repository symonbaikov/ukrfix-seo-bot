"""
Slug generation utilities with Ukrainian transliteration support.
"""

from __future__ import annotations

import re
from typing import Optional

try:
    from cyrtranslit import to_latin
except Exception:  # pragma: no cover - fallback when package is absent
    to_latin = None

# Basic Ukrainian → Latin mapping as a safe fallback
UA_MAP = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "h",
    "ґ": "g",
    "д": "d",
    "е": "e",
    "є": "ie",
    "ж": "zh",
    "з": "z",
    "и": "y",
    "і": "i",
    "ї": "yi",
    "й": "i",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ю": "yu",
    "я": "ya",
}


def _fallback_transliterate(text: str) -> str:
    transliterated = []
    for char in text:
        lower_char = char.lower()
        if lower_char in UA_MAP:
            value = UA_MAP[lower_char]
            transliterated.append(value)
        elif re.match(r"[a-z0-9]", lower_char):
            transliterated.append(lower_char)
        elif lower_char.isspace() or lower_char in "-_":
            transliterated.append(" ")
        # ignore other symbols
    return "".join(transliterated)


def transliterate_uk(text: str) -> str:
    """Transliterate Ukrainian text to Latin, using cyrtranslit if available."""
    if to_latin:
        try:
            return to_latin(text, "uk")
        except Exception:
            pass
    return _fallback_transliterate(text)


def generate_slug(text: str, max_length: int = 60) -> str:
    """
    Generate SEO-friendly slug.

    Steps:
        - transliterate Ukrainian → Latin
        - remove special symbols
        - enforce max length and collapse hyphens
    """
    transliterated = transliterate_uk(text)
    cleaned = re.sub(r"[^a-zA-Z0-9\s-]", "", transliterated)
    cleaned = cleaned.lower()
    cleaned = re.sub(r"\s+", "-", cleaned)
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")

    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip("-")

    return cleaned or "ukrfix-article"
