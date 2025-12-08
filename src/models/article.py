"""
Article data structures used across generation and publishing steps.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ArticleData:
    title: str
    html_content: str
    meta_description: str
    slug: str
    tags: List[str]
    category: str
    title_case: Optional[str] = None
    sentence_case: Optional[str] = None
