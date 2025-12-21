"""
SEO generator module - generates enriched articles via Google Gemini API.
Returns ArticleData with title, meta description, slug, tags and HTML content.
"""

from __future__ import annotations

import json
import random
import re
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from src.config import get_gemini_api_key, get_gemini_model_name
from src.models.article import ArticleData
from src.utils.content_enhancer import CTA_BUTTON, CTA_TEXT, ensure_cta_block
from src.utils.history import get_recent_titles
from src.utils.logger import log_error
from src.utils.slugify import extract_h1_text, generate_slug
from src.utils.title_optimizer import optimize_title


def _format_recent_titles(recent_titles: List[str]) -> str:
    if not recent_titles:
        return "немає записів"
    return "\n".join(f"- {title}" for title in recent_titles[-20:])


def _build_prompt(topic: str, country: str, city: str, category: str, google_info: str, recent_titles: List[str]) -> str:
    recent_titles_block = _format_recent_titles(recent_titles)
    return f"""
Ти редактор UkrFix.com. Підготуй SEO-статтю українською мовою та поверни лише JSON без коментарів або Markdown.

Тема: {topic}
Локація: {city}, {country}
Бізнес-напрям: {category}
Контекст з Google (коротко використай для фактів): 
{google_info}

Не дублюй ці заголовки:
{recent_titles_block}

Структура відповіді (поверни лише JSON):
{{
  "title": "SEO заголовок до 60 символів, без вступних фраз",
  "title_sentence": "Sentence case варіант того ж заголовка (до 60)",
  "meta_description": "140-160 символів, з CTR словами (⭐, найкраще, швидко, корисно)",
  "tags": ["5-8 коротких тегів українською"],
  "category": "Широка категорія для WordPress (напр. Авто з Польщі, Робота, Нерухомість, Послуги, Туризм)",
  "content": "<h1>...HTML стаття...</h1>"
}}

Вимоги до HTML:
- Використовуй <h1> для заголовка, h2/h3 підзаголовки, марковані списки <ul><li>, короткі абзаци по 2-3 речення.
- Додай приклад тексту оголошення у форматі списку або виділеного блоку.
- Структура повинна виглядати як у людини: списки, підзаголовки, короткі абзаци.
- Наприкінці додай CTA блок з фразою "{CTA_TEXT}" та кнопкою {CTA_BUTTON}.
""".strip()


def _extract_json_block(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
    if cleaned.lower().startswith("json"):
        cleaned = cleaned[4:].strip()

    try:
        return json.loads(cleaned)
    except Exception:
        match = re.search(r"\{.*\}", cleaned, re.S)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                return {}
    return {}


def _clean_html_content(html_content: str) -> str:
    html = html_content.strip()
    if html.startswith("```html"):
        html = html[7:].strip()
    elif html.startswith("```"):
        html = html[3:].strip()
    if html.endswith("```"):
        html = html[:-3].strip()
    return html


def _normalize_meta_description(meta: str, title: str) -> str:
    description = (meta or "").strip()
    if not description:
        description = f"{title} на UkrFix — ⭐ найкраще рішення, швидко та корисно для українців за кордоном."

    if "найкращ" not in description.lower():
        description = f"{description} Найкраще рішення від UkrFix."
    if "швид" not in description.lower():
        description = f"{description} Працюємо швидко."
    if "корис" not in description.lower():
        description = f"{description} Корисно для читачів."
    if "⭐" not in description:
        description = f"⭐ {description}"

    description = description.strip()
    if len(description) > 160:
        description = description[:157].rstrip(" ,;") + "..."
    elif len(description) < 140:
        description = f"{description} ⭐ Найкраще, швидко та корисно з UkrFix."
        if len(description) > 160:
            description = description[:157].rstrip(" ,;") + "..."
    return description


def _normalize_tags(raw_tags: Any, city: str, country: str, category: str) -> List[str]:
    tags: List[str] = []
    if isinstance(raw_tags, list):
        tags = [str(tag).strip() for tag in raw_tags if str(tag).strip()]

    # Ensure enough tags
    fallback = [category, city, country, "UkrFix", "оголошення"]
    for item in fallback:
        if len(tags) >= 8:
            break
        if item not in tags:
            tags.append(item)

    # Keep between 5 and 8 tags
    tags = tags[:8]
    if len(tags) < 5:
        extra = ["послуги", "поради", city]
        for item in extra:
            if len(tags) >= 5:
                break
            if item not in tags:
                tags.append(item)

    return tags


def generate_article(country: str, city: str, category: str, google_info: str, recent_titles: Optional[List[str]] = None) -> ArticleData:
    """
    Generate SEO article using Google Gemini API.
    
    Args:
        country: Country name
        city: City name
        category: Category name
        google_info: Context information from Google search
        recent_titles: Optional list of existing titles to avoid duplicates
        
    Returns:
        ArticleData with optimized title, meta description, slug, tags and HTML
    """
    recent_titles = recent_titles or get_recent_titles()

    # Determine article topic based on category type (Ukrainian)
    start_phrase = random.choice(["Як знайти", "Де знайти"])
    action = "клієнтів на"
    if "Продаж" in category or "Авто" in category:
        action = "покупців на"
    if "Оренда" in category:
        action = "орендарів на"
    topic = f"{start_phrase} {action} {category} в г. {city} ({country})"

    prompt = _build_prompt(topic, country, city, category, google_info, recent_titles)
    
    try:
        genai.configure(api_key=get_gemini_api_key())
        model_name = get_gemini_model_name()
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        payload = _extract_json_block(response.text)

        raw_title = payload.get("title") or topic
        chosen_title, title_case, sentence_case = optimize_title(raw_title)

        meta_description = _normalize_meta_description(payload.get("meta_description", ""), chosen_title)
        tags = _normalize_tags(payload.get("tags", []), city, country, category)
        wp_category = payload.get("category") or category

        html_content = _clean_html_content(payload.get("content", ""))
        if not html_content:
            html_content = _clean_html_content(response.text)
        html_content = ensure_cta_block(html_content)

        h1_text = extract_h1_text(html_content)
        slug_source = h1_text or payload.get("slug") or chosen_title
        slug = generate_slug(slug_source)

        return ArticleData(
            title=chosen_title,
            html_content=html_content,
            meta_description=meta_description,
            slug=slug,
            tags=tags,
            category=wp_category,
            title_case=title_case,
            sentence_case=sentence_case,
        )
    except Exception as e:
        error_msg = str(e)
        
        # Check for model not found errors (404)
        if "404" in error_msg or "not found" in error_msg.lower():
            log_error(f"Gemini API model not found: {error_msg}")
            log_error(f"Current model: {get_gemini_model_name()}")
            log_error("Please check available models at: https://ai.google.dev/models")
            log_error("Make sure GEMINI_MODEL is set to 'gemini-2.5-flash' in your environment variables")
        
        # Check for quota/billing errors
        if "429" in error_msg or "quota" in error_msg.lower() or "billing" in error_msg.lower():
            log_error(f"Gemini API quota/billing error: {error_msg}")
            log_error("The model may require a paid tier or quota is exceeded.")
            log_error(f"Current model: {get_gemini_model_name()}")
            log_error("Check your billing/quota at: https://ai.dev/usage?tab=rate-limit")
        
        log_error(f"Gemini API error: {e}")
        raise
