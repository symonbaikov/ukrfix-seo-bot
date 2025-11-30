"""
Configuration module - single point of access to environment variables.
All environment variable access must go through this module.
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


def get_wp_url() -> str:
    """Get WordPress URL from environment."""
    url = os.getenv("WP_URL")
    if not url:
        raise ValueError("WP_URL environment variable is not set")
    return url


def get_wp_username() -> str:
    """Get WordPress username from environment."""
    username = os.getenv("WP_USERNAME")
    if not username:
        raise ValueError("WP_USERNAME environment variable is not set")
    return username


def get_wp_app_password() -> str:
    """Get WordPress application password from environment."""
    password = os.getenv("WP_APP_PASSWORD")
    if not password:
        raise ValueError("WP_APP_PASSWORD environment variable is not set")
    return password


def get_openai_api_key() -> str:
    """Get OpenAI API key from environment."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    return key


def get_pexels_api_key() -> str:
    """Get Pexels API key from environment."""
    key = os.getenv("PEXELS_API_KEY")
    if not key:
        raise ValueError("PEXELS_API_KEY environment variable is not set")
    return key



