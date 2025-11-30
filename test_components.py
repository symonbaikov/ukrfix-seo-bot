"""
Test script to verify individual bot components.
Tests each module separately before full bot run.
"""

from src.config import (
    get_wp_url, get_wp_username, get_wp_app_password,
    get_gemini_api_key, get_pexels_api_key, get_gemini_model_name
)
from src.database import init_db, is_posted, mark_posted
from src.google_context import get_google_context
from src.image_service import get_pexels_image, upload_image_to_wp
from src.seo_generator import generate_article
from src.wp_publisher import publish_article
from src.models.location_map import LOCATIONS
from src.models.category_map import CATEGORIES
from src.utils.logger import log, log_success, log_error
import random


def test_database():
    """Test database operations."""
    log("\n=== Testing Database ===")
    try:
        init_db()
        log_success("Database initialized")
        
        # Test is_posted
        country = "Чехія"
        city = "Прага"
        category = "Ремонт квартир"
        
        is_already_posted = is_posted(country, city, category)
        log(f"is_posted check: {is_already_posted}")
        
        # Test mark_posted (only if not posted)
        if not is_already_posted:
            mark_posted(country, city, category)
            log_success("mark_posted executed")
            
            # Verify
            if is_posted(country, city, category):
                log_success("Database write/read verified")
            else:
                log_error("Database verification failed")
        else:
            log("Already posted, skipping mark_posted test")
        
        return True
    except Exception as e:
        log_error(f"Database test failed: {e}")
        return False


def test_google_search():
    """Test Google search functionality."""
    log("\n=== Testing Google Search ===")
    try:
        query = "оголошення ремонт квартир Прага Чехія форуми"
        context = get_google_context(query)
        
        if context and context != "Информация не найдена.":
            log_success(f"Google search returned context ({len(context)} chars)")
            log(f"Context preview: {context[:100]}...")
            return True
        else:
            log_error("Google search returned no results")
            return False
    except Exception as e:
        log_error(f"Google search test failed: {e}")
        return False


def test_pexels():
    """Test Pexels image search."""
    log("\n=== Testing Pexels API ===")
    try:
        query = "home renovation worker"
        image_url = get_pexels_image(query)
        
        if image_url:
            log_success(f"Pexels image found: {image_url[:50]}...")
            return True
        else:
            log_error("Pexels returned no image")
            return False
    except Exception as e:
        log_error(f"Pexels test failed: {e}")
        return False


def test_wordpress_connection():
    """Test WordPress REST API connection."""
    log("\n=== Testing WordPress Connection ===")
    try:
        import requests
        api_url = f"{get_wp_url()}/wp-json/wp/v2/posts"
        auth = (get_wp_username(), get_wp_app_password())
        
        # Try to get posts list (read-only operation)
        response = requests.get(
            f"{get_wp_url()}/wp-json/wp/v2/posts?per_page=1",
            auth=auth,
            timeout=10
        )
        
        if response.status_code == 200:
            log_success("WordPress REST API connection successful")
            return True
        else:
            log_error(f"WordPress connection failed: {response.status_code}")
            log_error(f"Response: {response.text[:200]}")
            return False
    except Exception as e:
        log_error(f"WordPress connection test failed: {e}")
        return False


def test_gemini():
    """Test Google Gemini API (minimal test)."""
    log("\n=== Testing Google Gemini API ===")
    try:
        import google.generativeai as genai
        
        # Configure Gemini
        genai.configure(api_key=get_gemini_api_key())
        model_name = get_gemini_model_name()
        model = genai.GenerativeModel(model_name)
        
        # Simple test request
        response = model.generate_content("Say 'OK' if you can read this.")
        
        result = response.text.strip()
        log_success(f"Gemini API working: {result}")
        log(f"Model used: {model_name}")
        return True
    except Exception as e:
        log_error(f"Gemini test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_workflow_draft():
    """Test full workflow but save as draft instead of publishing."""
    log("\n=== Testing Full Workflow (DRAFT MODE) ===")
    
    try:
        # Select a random combination
        country = random.choice(list(LOCATIONS.keys()))
        city = random.choice(LOCATIONS[country])
        category = random.choice(list(CATEGORIES.keys()))
        
        log(f"Selected: {category} in {city}, {country}")
        
        # 1. Google context
        search_query = f"оголошення {category} {city} {country} форуми"
        log("Getting Google context...")
        google_context = get_google_context(search_query)
        log_success("Google context retrieved")
        
        # 2. Image
        img_query = CATEGORIES[category]
        log("Searching for image...")
        img_url = get_pexels_image(img_query)
        image_id = None
        
        if img_url:
            log("Uploading image to WordPress...")
            image_id = upload_image_to_wp(img_url, f"TEST: {category} {city}")
            if image_id:
                log_success(f"Image uploaded, ID: {image_id}")
            else:
                log_error("Image upload failed")
        else:
            log_error("No image found")
        
        # 3. Generate article
        log("Generating article...")
        title, html_content = generate_article(country, city, category, google_context)
        log_success(f"Article generated: {title}")
        log(f"Content length: {len(html_content)} chars")
        
        # 4. Publish as DRAFT (test mode)
        log("Publishing as DRAFT (test mode)...")
        import requests
        api_url = f"{get_wp_url()}/wp-json/wp/v2/posts"
        auth = (get_wp_username(), get_wp_app_password())
        
        data = {
            'title': f"[TEST] {title}",
            'content': html_content,
            'status': 'draft'  # DRAFT instead of publish
        }
        
        if image_id:
            data['featured_media'] = image_id
        
        response = requests.post(
            api_url,
            json=data,
            auth=auth,
            timeout=30
        )
        
        if response.status_code == 201:
            post_id = response.json()['id']
            log_success(f"Article saved as DRAFT! Post ID: {post_id}")
            log(f"View draft: {get_wp_url()}/wp-admin/post.php?post={post_id}&action=edit")
            return True
        else:
            log_error(f"Publish failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        log_error(f"Full workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    log("=" * 60)
    log("BOT COMPONENT TESTING")
    log("=" * 60)
    
    results = {}
    
    # Individual component tests
    results['database'] = test_database()
    results['google'] = test_google_search()
    results['pexels'] = test_pexels()
    results['wordpress'] = test_wordpress_connection()
    results['gemini'] = test_gemini()
    
    # Summary
    log("\n" + "=" * 60)
    log("TEST SUMMARY")
    log("=" * 60)
    
    for component, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        log(f"{component.upper():15} {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        log_success("\nAll component tests passed!")
        
        # Ask about full workflow test
        log("\n" + "=" * 60)
        log("FULL WORKFLOW TEST (DRAFT MODE)")
        log("=" * 60)
        log("This will create a draft article in WordPress.")
        log("Continue? (This will test the complete workflow)")
        
        try:
            response = input("Run full workflow test? (y/n): ").strip().lower()
            if response == 'y':
                test_full_workflow_draft()
            else:
                log("Skipping full workflow test.")
        except KeyboardInterrupt:
            log("\nTest interrupted by user.")
    else:
        log_error("\nSome tests failed. Please fix issues before running the bot.")
        log("Failed components:")
        for component, passed in results.items():
            if not passed:
                log_error(f"  - {component}")


if __name__ == "__main__":
    main()


