"""
WordPress publisher module - publishes articles to WordPress.
Handles errors gracefully without crashing the bot.
"""

from typing import Optional
import requests
from src.config import get_wp_url, get_wp_username, get_wp_app_password
from src.utils.logger import log_error, log_success


def publish_article(title: str, content: str, featured_media_id: Optional[int] = None) -> None:
    """
    Publish article to WordPress via REST API.
    
    Args:
        title: Article title
        content: Article HTML content
        featured_media_id: Optional WordPress media ID for featured image
    """
    try:
        api_url = f"{get_wp_url()}/wp-json/wp/v2/posts"
        auth = (get_wp_username(), get_wp_app_password())
        
        data = {
            'title': title,
            'content': content,
            'status': 'publish'
        }
        
        if featured_media_id:
            data['featured_media'] = featured_media_id
        
        response = requests.post(
            api_url,
            json=data,
            auth=auth,
            timeout=30
        )
        
        if response.status_code == 201:
            log_success(f"Article published: {title}")
        else:
            log_error(f"WordPress publish failed: {response.status_code} - {response.text}")
    except Exception as e:
        log_error(f"Publish article failed: {e}")



