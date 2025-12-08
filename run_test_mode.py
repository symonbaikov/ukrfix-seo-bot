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
from src.utils.content_enhancer import inject_internal_links
from src.utils.history import find_internal_links, get_recent_titles, is_duplicate_title, load_history
from src.wp_publisher import publish_article


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

    history_records = load_history()
    
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
            recent_titles = get_recent_titles(history_records)
            article = generate_article(country, city, category, google_context, recent_titles)

            if is_duplicate_title(article.title, history_records):
                log_error(f"Duplicate title detected, skipping: {article.title}")
                time.sleep(10)
                continue

            internal_links = find_internal_links(article, history_records)
            article.html_content = inject_internal_links(article.html_content, internal_links)

            # Make draft-specific markers to avoid URL collisions
            article.title = f"[TEST] {article.title}"
            article.slug = f"test-{article.slug}"
            
            # 5. Publish as DRAFT (test mode)
            log("Publishing as DRAFT...")
            success = publish_article(article, image_id, status='draft')
            
            if success:
                # 6. Mark as posted (even though it's draft, to avoid duplicates in test)
                mark_posted(country, city, category)
                history_records.append(
                    {
                        "title": article.title,
                        "slug": article.slug,
                        "url": "",
                        "tags": article.tags,
                        "category": article.category,
                    }
                )
                article_count += 1
                log_success(f"Done! Article '{article.title}' saved as DRAFT.")
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


