"""
Image service module - handles Pexels API and WordPress media upload.
No text generation or post publishing logic here.
"""

import random
import requests
from typing import Optional
from src.config import get_pexels_api_key, get_wp_url, get_wp_username, get_wp_app_password
from src.utils.logger import log_error


def get_pexels_image(query: str) -> Optional[str]:
    """
    Search Pexels for an image and return its URL.
    
    Args:
        query: Search query for image (in English)
        
    Returns:
        Image URL or None if not found
    """
    try:
        headers = {'Authorization': get_pexels_api_key()}
        url = f"https://api.pexels.com/v1/search?query={query}&per_page=1&orientation=landscape"
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get('photos'):
            return data['photos'][0]['src']['large']
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
            'Content-Type': 'image/jpeg',
            'Content-Disposition': f'attachment; filename={filename}'
        }
        
        # Upload to WordPress
        api_url = f"{get_wp_url()}/wp-json/wp/v2/media"
        response = requests.post(
            api_url,
            data=img_data,
            headers=headers,
            auth=auth,
            timeout=30
        )
        
        if response.status_code == 201:
            return response.json()['id']
        else:
            log_error(f"WordPress upload failed: {response.status_code} - {response.text}")
    except Exception as e:
        log_error(f"Image upload failed: {e}")
    
    return None




