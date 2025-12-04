"""
Test mode bot runner - publishes articles as DRAFT with short intervals.
Use this for testing before production run.
"""

import time
import random
from src.database import init_db, is_posted, mark_posted
from src.models.location_map import LOCATIONS
from src.models.category_map import CATEGORIES
from src.google_context import get_google_context
from src.image_service import get_pexels_image, upload_image_to_wp
from src.seo_generator import generate_article
from src.utils.logger import log, log_error, log_success
import requests
from src.config import get_wp_url, get_wp_username, get_wp_app_password


def publish_as_draft(title: str, content: str, featured_media_id=None):
    """Publish article as DRAFT instead of publish."""
    try:
        api_url = f"{get_wp_url()}/wp-json/wp/v2/posts"
        auth = (get_wp_username(), get_wp_app_password())
        
        data = {
            'title': f"[TEST] {title}",
            'content': content,
            'status': 'draft'  # DRAFT mode
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
            post_id = response.json()['id']
            log_success(f"Article saved as DRAFT! Post ID: {post_id}")
            log(f"View: {get_wp_url()}/wp-admin/post.php?post={post_id}&action=edit")
            return True
        else:
            log_error(f"Publish failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        log_error(f"Publish article failed: {e}")
        return False


def select_task(max_attempts: int = 100):
    """Select a random combination that hasn't been posted yet."""
    attempts = 0
    while attempts < max_attempts:
        country = random.choice(list(LOCATIONS.keys()))
        city = random.choice(LOCATIONS[country])
        category = random.choice(list(CATEGORIES.keys()))
        
        if not is_posted(country, city, category):
            return country, city, category
        
        attempts += 1
    
    return None


def main():
    """
    Test mode bot - publishes as DRAFT with short intervals (1-2 minutes).
    """
    # Initialize
    try:
        init_db()
        log("=" * 60)
        log("BOT TEST MODE - Articles will be saved as DRAFT")
        log("=" * 60)
        log("Bot started for UkrFix (TEST MODE)!")
    except Exception as e:
        log_error(f"Initialization failed: {e}")
        return
    
    article_count = 0
    max_test_articles = 3  # Limit for testing
    
    while article_count < max_test_articles:
        try:
            # 1. Select task
            task = select_task()
            if not task:
                log("All combinations posted! Sleeping for 1 hour...")
                time.sleep(3600)
                continue
            
            country, city, category = task
            log(f"\n[{article_count + 1}/{max_test_articles}] Working on: {category} in {city}, {country}")
            
            # 2. Get Google context
            search_query = f"оголошення {category} {city} {country} форуми"
            google_context = get_google_context(search_query)
            
            # 3. Get and upload image
            img_query = CATEGORIES[category]
            img_url = get_pexels_image(img_query)
            image_id = None
            
            if img_url:
                log("Image found, uploading...")
                image_id = upload_image_to_wp(img_url, f"{category} {city}")
            
            # 4. Generate article
            log("Generating article...")
            title, html_content = generate_article(country, city, category, google_context)
            
            # 5. Publish as DRAFT (test mode)
            log("Publishing as DRAFT...")
            success = publish_as_draft(title, html_content, image_id)
            
            if success:
                # 6. Mark as posted (even though it's draft, to avoid duplicates in test)
                mark_posted(country, city, category)
                article_count += 1
                log_success(f"Done! Article '{title}' saved as DRAFT.")
            else:
                log_error("Failed to save article. Skipping mark_posted.")
            
            # 7. Short sleep for testing (1-2 minutes instead of 80-100)
            if article_count < max_test_articles:
                wait_time = random.randint(60, 120)  # 1-2 minutes
                log(f"Sleeping {wait_time} seconds until next article...")
                time.sleep(wait_time)
            
        except KeyboardInterrupt:
            log("\nBot stopped by user")
            break
        except Exception as e:
            log_error(f"Error in main loop: {e}")
            log("Sleeping 30 seconds before retry...")
            time.sleep(30)
    
    log("\n" + "=" * 60)
    log_success(f"Test mode completed! Created {article_count} draft articles.")
    log("Check WordPress admin panel to review drafts.")
    log("=" * 60)


if __name__ == "__main__":
    main()



