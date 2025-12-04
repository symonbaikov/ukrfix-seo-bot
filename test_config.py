"""
Test script to verify bot configuration before running.
Checks if all required environment variables are set.
"""

from src.config import (
    get_wp_url,
    get_wp_username,
    get_wp_app_password,
    get_openai_api_key,
    get_pexels_api_key
)
from src.utils.logger import log, log_success, log_error


def test_config():
    """Test if all configuration variables are set."""
    log("Testing bot configuration...")
    
    errors = []
    
    try:
        wp_url = get_wp_url()
        if "your_" in wp_url or "example" in wp_url.lower():
            errors.append("WP_URL appears to be a placeholder")
        else:
            log_success(f"WP_URL: {wp_url}")
    except Exception as e:
        errors.append(f"WP_URL: {e}")
    
    try:
        wp_user = get_wp_username()
        if "your_" in wp_user or "example" in wp_user.lower():
            errors.append("WP_USERNAME appears to be a placeholder")
        else:
            log_success(f"WP_USERNAME: {wp_user}")
    except Exception as e:
        errors.append(f"WP_USERNAME: {e}")
    
    try:
        wp_pass = get_wp_app_password()
        if "your_" in wp_pass or "example" in wp_pass.lower() or len(wp_pass) < 10:
            errors.append("WP_APP_PASSWORD appears to be invalid")
        else:
            log_success("WP_APP_PASSWORD: ✓ (hidden)")
    except Exception as e:
        errors.append(f"WP_APP_PASSWORD: {e}")
    
    try:
        openai_key = get_openai_api_key()
        if "sk-proj-..." in openai_key or "your_" in openai_key or len(openai_key) < 20:
            errors.append("OPENAI_API_KEY appears to be invalid")
        else:
            log_success("OPENAI_API_KEY: ✓ (hidden)")
    except Exception as e:
        errors.append(f"OPENAI_API_KEY: {e}")
    
    try:
        pexels_key = get_pexels_api_key()
        if "your_" in pexels_key or "example" in pexels_key.lower() or len(pexels_key) < 10:
            errors.append("PEXELS_API_KEY appears to be invalid")
        else:
            log_success("PEXELS_API_KEY: ✓ (hidden)")
    except Exception as e:
        errors.append(f"PEXELS_API_KEY: {e}")
    
    if errors:
        log_error("Configuration errors found:")
        for error in errors:
            log_error(f"  - {error}")
        log("\nPlease update your .env file with real values.")
        return False
    else:
        log_success("\n✓ All configuration variables are set correctly!")
        log("Bot is ready to run!")
        return True


if __name__ == "__main__":
    test_config()



