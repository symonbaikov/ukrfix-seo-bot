"""
Utility helpers to normalize and optimize titles for SEO.
"""

from __future__ import annotations

import re
from typing import Tuple

# Common Ukrainian stop words that do not add value to headlines
STOP_WORDS = {
    "і",
    "й",
    "та",
    "а",
    "але",
    "чи",
    "або",
    "у",
    "в",
    "з",
    "із",
    "зі",
    "за",
    "як",
    "що",
    "для",
    "про",
    "на",
    "до",
    "без",
    "при",
    "під",
    "над",
    "через",
    "після",
}


def _clean_text(text: str) -> str:
    """Trim spaces and stray punctuation."""
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    cleaned = cleaned.strip("-–—:;,.")
    return cleaned


def _trim_stop_words(text: str) -> str:
    """Remove stop words from the beginning of the string only."""
    words = text.split()
    while words and words[0].lower() in STOP_WORDS:
        words.pop(0)
    return " ".join(words)


def _to_sentence_case(text: str) -> str:
    """Convert string to sentence case."""
    cleaned = _clean_text(text)
    if not cleaned:
        return ""
    return cleaned[0].upper() + cleaned[1:]


def _to_title_case(text: str) -> str:
    """Convert string to title case while skipping stop words in the middle."""
    words = _clean_text(text).split()
    title_words = []
    for idx, word in enumerate(words):
        lower_word = word.lower()
        if idx != 0 and lower_word in STOP_WORDS:
            title_words.append(lower_word)
        else:
            title_words.append(word[:1].upper() + word[1:])
    return " ".join(title_words)


def _truncate(text: str, limit: int) -> str:
    """Trim text to limit, keeping whole words when possible."""
    if len(text) <= limit:
        return text
    cut = text[:limit]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    cut = cut.rstrip("-–—:;,")
    suffix = "..."
    trimmed = f"{cut}{suffix}"
    if len(trimmed) > limit:
        trimmed = trimmed[:limit]
    return trimmed


def optimize_title(raw_title: str, max_length: int = 60) -> Tuple[str, str, str]:
    """
    Produce SEO-friendly title variants and choose the best fit.

    Returns:
        tuple of (chosen_title, title_case, sentence_case)
    """
    base = _trim_stop_words(_clean_text(raw_title))
    sentence_case = _truncate(_to_sentence_case(base), max_length)
    title_case = _truncate(_to_title_case(base), max_length)

    # Prefer title case if it fits, otherwise fall back to the shorter option
    preferred = title_case if len(title_case) <= max_length else sentence_case
    if not preferred:
        preferred = "UkrFix: нова стаття"
    return preferred, title_case or preferred, sentence_case or preferred
