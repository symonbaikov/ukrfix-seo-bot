"""
Image service module - handles Pexels API and WordPress media upload.
Adds relevancy filtering, horizontal preference and size optimization.
"""

import random
import re
from typing import Optional

import requests

from src.config import get_pexels_api_key, get_wp_app_password, get_wp_url, get_wp_username
from src.utils.logger import log_error


def _score_photo(photo: dict, keywords: list[str]) -> int:
    score = 0
    alt = photo.get("alt", "").lower()
    for word in keywords:
        if word in alt:
            score += 2
    if photo.get("width", 0) >= photo.get("height", 0):
        score += 1
    return score


def get_pexels_image(query: str) -> Optional[str]:
    """
    Search Pexels for an image and return its URL.
    
    Args:
        query: Search query for image (in English)
        
    Returns:
        Image URL or None if not found
    """
    try:
        headers = {"Authorization": get_pexels_api_key()}
        params = {
            "query": query,
            "per_page": 8,
            "orientation": "landscape",
            "size": "large",
        }
        url = "https://api.pexels.com/v1/search"
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        photos = data.get("photos", [])
        if not photos:
            return None

        keywords = [word.lower() for word in re.split(r"\\s+", query) if len(word) > 2]
        best_photo = max(photos, key=lambda p: _score_photo(p, keywords))
        sources = best_photo.get("src", {})
        # Prefer optimized sizes to avoid huge files
        return sources.get("large") or sources.get("medium") or sources.get("large2x") or sources.get("original")
    except Exception as e:
        log_error(f"Pexels API error: {e}")
    
    return None


def upload_image_to_wp(image_url: str, title: str) -> Optional[int]:
    """
    Download image from URL and upload it to WordPress media library.
    
    Args:
        image_url: URL of the image to download
        title: Title for the image
        
    Returns:
        WordPress media ID or None if upload failed
    """
    try:
        # Download image
        img_response = requests.get(image_url, timeout=30)
        img_response.raise_for_status()
        img_data = img_response.content
        
        # Generate filename
        filename = f"{random.randint(1000, 9999)}_image.jpg"
        
        # WordPress API authentication
        auth = (get_wp_username(), get_wp_app_password())
        headers = {
            "Content-Type": "image/jpeg",
            "Content-Disposition": f"attachment; filename={filename}",
        }
        
        # Upload to WordPress
        api_url = f"{get_wp_url()}/wp-json/wp/v2/media"
        response = requests.post(
            api_url,
            data=img_data,
            headers=headers,
            auth=auth,
            timeout=30,
        )
        
        if response.status_code == 201:
            return response.json()["id"]
        else:
            log_error(f"WordPress upload failed: {response.status_code} - {response.text}")
    except Exception as e:
        log_error(f"Image upload failed: {e}")
    
    return None





