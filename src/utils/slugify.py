"""
Slug generation utilities with Ukrainian transliteration support.

Rules:
- Use H1/title text as source, transliterate to Latin, keep words readable.
- Strip stop words/special symbols, collapse hyphens, and cap length.
- Keep 3–5 meaningful keywords when headings are long; avoid template slugs.
"""

from __future__ import annotations

import re
from typing import Iterable, List, Optional

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

STOP_WORDS = {
    # Ukrainian (transliterated) stop words
    "i",
    "ta",
    "a",
    "y",
    "yi",
    "yiyi",
    "ale",
    "abo",
    "chi",
    "pro",
    "dlia",
    "dla",
    "dlya",
    "na",
    "u",
    "v",
    "za",
    "vid",
    "do",
    "po",
    "pid",
    "nad",
    "pid",
    "pere",
    "yak",
    "tse",
    "ce",
    "hto",
    "khto",
    "tylki",
    "tilky",
    "tilki",
    "te",
    "tsya",
    "tsyi",
    "tsye",
    "miz",
    "miz",
    "z",
    "iz",
    # English stop words
    "the",
    "and",
    "or",
    "for",
    "of",
    "to",
    "in",
    "on",
    "with",
    "by",
    "from",
    "a",
    "an",
    "how",
    "where",
    "what",
    "why",
    "when",
    "best",
    "top",
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
            converted = to_latin(text, "uk")
            # cyrtranslit may return original text for mixed/unknown chars; fallback if Cyrillic remains
            if re.search(r"[\\u0400-\\u04FF]", converted):
                return _fallback_transliterate(text)
            return converted
        except Exception:
            pass
    return _fallback_transliterate(text)


def _tokenize(text: str) -> List[str]:
    cleaned = re.sub(r"[^a-zA-Z0-9\s_-]", " ", text)
    parts = re.split(r"[\s_-]+", cleaned.lower())
    return [part for part in parts if part]


def _filter_stop_words(words: Iterable[str]) -> List[str]:
    filtered: List[str] = []
    seen = set()
    for word in words:
        if word in STOP_WORDS:
            continue
        if word in seen:
            continue
        seen.add(word)
        filtered.append(word)
    return filtered


def _trim_keywords(words: List[str], max_words: int = 5) -> List[str]:
    """Keep 3–5 meaningful keywords when source is long."""
    if len(words) <= max_words:
        return words
    trimmed = words[:max_words]
    return trimmed if len(trimmed) >= 3 else words[:3]


def _collapse_hyphens(slug: str) -> str:
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def _looks_like_template(slug: str) -> bool:
    return bool(re.match(r"^(article|post|page|blog)-\d+$", slug))


def generate_slug(text: str, max_length: int = 75) -> str:
    """
    Generate SEO-friendly slug.

    Steps:
        - transliterate Ukrainian → Latin
        - drop stop words/special symbols
        - keep 3–5 meaningful keywords when heading is long
        - enforce max length and collapse hyphens
    """
    transliterated = transliterate_uk(text)
    tokens = _tokenize(transliterated)
    meaningful = _filter_stop_words(tokens)
    if not meaningful:
        meaningful = tokens

    meaningful = _trim_keywords(meaningful)
    slug = _collapse_hyphens("-".join(meaningful))

    if len(slug) > max_length:
        slug = slug[:max_length]
        slug = _collapse_hyphens(slug)

    if _looks_like_template(slug) or not slug:
        slug = "ukrfix-article"

    return slug or "ukrfix-article"


def extract_h1_text(html: str) -> Optional[str]:
    """
    Extract first <h1>...</h1> text for slug source.
    Strips nested tags to keep plain text.
    """
    if not html:
        return None
    match = re.search(r"<h1[^>]*>(.*?)</h1>", html, flags=re.I | re.S)
    if not match:
        return None
    h1 = match.group(1)
    h1 = re.sub(r"<[^>]+>", " ", h1)
    h1 = re.sub(r"\s+", " ", h1).strip()
    return h1 or None
