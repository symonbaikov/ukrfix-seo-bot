"""
Test script to verify Gemini article generation.
Tests the full article generation workflow with Gemini API.
"""

import os
from dotenv import load_dotenv
from src.seo_generator import generate_article
from src.config import get_gemini_api_key, get_gemini_model_name
from src.utils.logger import log, log_success, log_error

# Load environment variables
load_dotenv()


def test_gemini_article_generation():
    """Test article generation with Gemini API."""
    log("=" * 60)
    log("TESTING GEMINI ARTICLE GENERATION")
    log("=" * 60)
    
    # Check API key
    try:
        api_key = get_gemini_api_key()
        log_success(f"Gemini API key found: {api_key[:10]}...")
    except Exception as e:
        log_error(f"Failed to get Gemini API key: {e}")
        log("Please set GEMINI_API_KEY in your .env file")
        return False
    
    # Check model name
    model_name = get_gemini_model_name()
    log(f"Using model: {model_name}")
    
    # Test parameters
    country = "Чехія"
    city = "Прага"
    category = "Ремонт квартир"
    google_info = "Прага - столица Чехии. Здесь активный рынок ремонтных услуг. Много украинских специалистов."
    
    log("\n" + "-" * 60)
    log(f"Test parameters:")
    log(f"  Country: {country}")
    log(f"  City: {city}")
    log(f"  Category: {category}")
    log(f"  Google info: {google_info[:50]}...")
    log("-" * 60)
    
    # Test article generation
    try:
        log("\nGenerating article with Gemini...")
        title, html_content = generate_article(
            country=country,
            city=city,
            category=category,
            google_info=google_info
        )
        
        log_success("Article generated successfully!")
        log(f"\nTitle: {title}")
        log(f"Content length: {len(html_content)} characters")
        log(f"\nContent preview (first 500 chars):")
        log("-" * 60)
        log(html_content[:500])
        log("-" * 60)
        
        # Basic validation
        if not title or len(title) < 10:
            log_error("Title seems too short")
            return False
        
        if not html_content or len(html_content) < 500:
            log_error("Content seems too short")
            return False
        
        if "ukrfix.com" not in html_content.lower():
            log_error("Content doesn't contain UkrFix reference")
            return False
        
        log_success("\n✅ All validations passed!")
        return True
        
    except Exception as e:
        log_error(f"Article generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_gemini_article_generation()
    
    log("\n" + "=" * 60)
    if success:
        log_success("TEST PASSED: Gemini article generation works!")
    else:
        log_error("TEST FAILED: Please check the errors above")
    log("=" * 60)


