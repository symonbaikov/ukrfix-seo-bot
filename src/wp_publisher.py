"""
WordPress publisher module - publishes articles to WordPress.
Handles errors gracefully without crashing the bot.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

import requests

from src.config import get_wp_app_password, get_wp_url, get_wp_username
from src.models.article import ArticleData
from src.utils.logger import log, log_error, log_success

TERM_CACHE: Dict[str, Dict[str, int]] = {"tags": {}, "categories": {}}


def _auth():
    return get_wp_username(), get_wp_app_password()


def _find_term_id(name: str, taxonomy: str) -> Optional[int]:
    """Search WP for an existing term by name."""
    cached = TERM_CACHE.get(taxonomy, {}).get(name.lower())
    if cached:
        return cached

    try:
        url = f"{get_wp_url()}/wp-json/wp/v2/{taxonomy}"
        response = requests.get(
            url,
            params={"search": name, "per_page": 50},
            auth=_auth(),
            timeout=15,
        )
        if response.status_code == 200:
            for item in response.json():
                if item.get("name", "").lower() == name.lower():
                    TERM_CACHE[taxonomy][name.lower()] = item["id"]
                    return item["id"]
    except Exception as e:
        log_error(f"Failed to search {taxonomy}: {e}")
    return None


def _create_term(name: str, taxonomy: str) -> Optional[int]:
    """Create a new term if it does not exist."""
    try:
        url = f"{get_wp_url()}/wp-json/wp/v2/{taxonomy}"
        response = requests.post(
            url,
            json={"name": name},
            auth=_auth(),
            timeout=15,
        )
        if response.status_code in (200, 201):
            term_id = response.json().get("id")
            if term_id:
                TERM_CACHE[taxonomy][name.lower()] = term_id
            return term_id
        else:
            log_error(f"Failed to create {taxonomy} '{name}': {response.status_code} - {response.text}")
    except Exception as e:
        log_error(f"Error creating {taxonomy} '{name}': {e}")
    return None


def _ensure_terms(names: List[str], taxonomy: str) -> List[int]:
    term_ids: List[int] = []
    for name in names:
        if not name:
            continue
        term_id = _find_term_id(name, taxonomy)
        if not term_id:
            term_id = _create_term(name, taxonomy)
        if term_id:
            term_ids.append(term_id)
    return term_ids


def publish_article(article: ArticleData, featured_media_id: Optional[int] = None, status: str = "publish") -> Optional[Dict]:
    """
    Publish article to WordPress via REST API.
    
    Args:
        article: Prepared article data
        featured_media_id: Optional WordPress media ID for featured image
        status: Post status ('publish', 'draft', 'pending'). Default: 'publish'
    """
    try:
        post_status = os.getenv("WP_POST_STATUS", status)

        api_url = f"{get_wp_url()}/wp-json/wp/v2/posts"
        auth = _auth()

        tag_ids = _ensure_terms(article.tags, "tags")
        category_ids = _ensure_terms([article.category], "categories") if article.category else []

        data = {
            "title": article.title,
            "content": article.html_content,
            "status": post_status,
            "slug": article.slug,
            "excerpt": article.meta_description,
        }

        if featured_media_id:
            data["featured_media"] = featured_media_id
        if tag_ids:
            data["tags"] = tag_ids
        if category_ids:
            data["categories"] = category_ids

        response = requests.post(
            api_url,
            json=data,
            auth=auth,
            timeout=30,
        )

        if response.status_code == 201:
            post_data = response.json()
            post_id = post_data.get("id", "N/A")
            link = post_data.get("link", "")
            if post_status == "draft":
                log_success(f"Article saved as DRAFT: {article.title} (ID: {post_id})")
                if link:
                    log(f"Draft preview: {link}")
            else:
                log_success(f"Article published: {article.title} (ID: {post_id})")
                if link:
                    log(f"View: {link}")
            return post_data
        else:
            log_error(f"WordPress publish failed: {response.status_code} - {response.text}")
    except Exception as e:
        log_error(f"Publish article failed: {e}")
    return None

