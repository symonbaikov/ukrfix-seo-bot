"""
Bot orchestrator - main loop and coordination logic.
No API details here, only calls to other modules.
"""

import time
import random
from src.database import init_db, is_posted, mark_posted
from src.models.location_map import LOCATIONS
from src.models.category_map import CATEGORIES
from src.google_context import get_google_context
from src.image_service import get_pexels_image, upload_image_to_wp
from src.seo_generator import generate_article
from src.wp_publisher import publish_article
from src.utils.content_enhancer import inject_internal_links
from src.utils.history import (
    add_article_record,
    find_internal_links,
    get_recent_titles,
    is_duplicate_title,
    load_history,
)
from src.utils.logger import log, log_error, log_success
from src.config import get_wp_url


def select_task(max_attempts: int = 100) -> tuple[str, str, str] | None:
    """
    Select a random combination of country, city, category that hasn't been posted yet.
    
    Args:
        max_attempts: Maximum number of attempts to find unposted combination
        
    Returns:
        Tuple of (country, city, category) or None if not found
    """
    attempts = 0
    while attempts < max_attempts:
        country = random.choice(list(LOCATIONS.keys()))
        city = random.choice(LOCATIONS[country])
        category = random.choice(list(CATEGORIES.keys()))
        
        if not is_posted(country, city, category):
            return country, city, category
        
        attempts += 1
    
    return None


def main() -> None:
    """
    Main bot loop - orchestrates the entire workflow.
    """
    # Initialize
    try:
        init_db()
        log("Bot started for UkrFix!")
    except Exception as e:
        log_error(f"Initialization failed: {e}")
        return

    history_records = load_history()
    
    while True:
        try:
            # 1. Select task
            task = select_task()
            if not task:
                log("All combinations posted! Sleeping for 1 hour...")
                time.sleep(3600)
                continue
            
            country, city, category = task
            log(f"Working on: {category} in {city}, {country}")
            
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
            
            # 5. Publish article
            log("Publishing...")
            result = publish_article(article, image_id)
            if not result:
                log_error("Publishing failed, will retry later.")
                time.sleep(300)
                continue
            
            # 6. Mark as posted
            mark_posted(country, city, category)
            history_records = add_article_record(article, get_wp_url(), history_records)
            log_success(f"Done! Article '{article.title}' published.")
            
            # 7. Sleep (80-100 minutes for ~15 articles per day)
            wait_time = random.randint(4800, 6000)
            log(f"Sleeping {wait_time/60:.1f} minutes until next article...")
            time.sleep(wait_time)
            
        except KeyboardInterrupt:
            log("Bot stopped by user")
            break
        except Exception as e:
            log_error(f"Error in main loop: {e}")
            log("Sleeping 10 minutes before retry...")
            time.sleep(600)
