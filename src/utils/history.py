"""
Helpers for storing and reusing published article metadata.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from src.models.article import ArticleData

DATA_DIR = Path("data")
HISTORY_FILE = DATA_DIR / "published_articles.json"


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[\w']+", text.lower())
    return set(tokens)


def load_history() -> List[Dict]:
    """Load stored article metadata."""
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def save_history(records: List[Dict]) -> None:
    """Persist history to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as fp:
        json.dump(records, fp, ensure_ascii=False, indent=2)


def get_recent_titles(records: Optional[List[Dict]] = None, limit: int = 50) -> List[str]:
    """Return the most recent titles for prompting uniqueness."""
    records = records if records is not None else load_history()
    return [rec.get("title", "") for rec in records][-limit:]


def is_duplicate_title(title: str, records: Optional[List[Dict]] = None) -> bool:
    """Simple duplicate title checker."""
    records = records if records is not None else load_history()
    normalized = title.lower().strip()
    return any(normalized == rec.get("title", "").lower().strip() for rec in records)


def add_article_record(article: ArticleData, wp_url: str, records: Optional[List[Dict]] = None) -> List[Dict]:
    """Append a new article entry to history."""
    records = records if records is not None else load_history()
    url = f"{wp_url.rstrip('/')}/{article.slug.strip('/')}/"

    # Skip if slug already exists
    if any(rec.get("slug") == article.slug for rec in records):
        return records

    record = {
        "title": article.title,
        "slug": article.slug,
        "url": url,
        "tags": article.tags,
        "category": article.category,
    }
    records.append(record)
    save_history(records)
    return records


def find_internal_links(article: ArticleData, records: Optional[List[Dict]] = None, max_links: int = 2) -> List[Dict[str, str]]:
    """Pick 1-2 relevant internal links from history."""
    records = records if records is not None else load_history()
    if not records:
        return []

    article_tokens = set(t.lower() for t in article.tags)
    article_tokens.update(_tokenize(article.title))
    article_tokens.add(article.category.lower())

    scored: List[tuple[int, Dict]] = []
    for rec in reversed(records):  # prefer recent posts
        if rec.get("slug") == article.slug:
            continue

        url = rec.get("url")
        if not url:
            continue

        rec_tokens = set(t.lower() for t in rec.get("tags", []))
        rec_tokens.update(_tokenize(rec.get("title", "")))
        if rec.get("category"):
            rec_tokens.add(rec["category"].lower())

        overlap = len(article_tokens & rec_tokens)
        if overlap == 0:
            continue

        score = overlap
        if rec.get("category", "").lower() == article.category.lower():
            score += 1

        scored.append((score, rec))

    scored.sort(key=lambda item: item[0], reverse=True)
    selected = []
    for _, rec in scored[:max_links]:
        selected.append({"title": rec.get("title", ""), "url": rec.get("url", "")})
    return selected
