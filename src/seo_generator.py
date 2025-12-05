"""
SEO generator module - generates articles via Google Gemini API.
Returns tuple of (title, html_content).
"""

import google.generativeai as genai
from src.config import get_gemini_api_key, get_gemini_model_name
from src.utils.logger import log_error
import random


def generate_article(country: str, city: str, category: str, google_info: str) -> tuple[str, str]:
    """
    Generate SEO article using Google Gemini API.
    
    Args:
        country: Country name
        city: City name
        category: Category name
        google_info: Context information from Google search
        
    Returns:
        Tuple of (title, html_content)
    """
    # Determine article topic based on category type (Ukrainian)
    # Use "Як знайти" or "Де знайти" randomly
    start_phrase = random.choice(["Як знайти", "Де знайти"])
    
    action = "клієнтів на"
    if "Продаж" in category or "Авто" in category:
        action = "покупців на"
    if "Оренда" in category:
        action = "орендарів на"
    
    topic = f"{start_phrase} {action} {category} в г. {city} ({country})"
    
    prompt = f"""
Створи SEO-статтю для UkrFix.com на тему: {topic}

ВАЖЛИВО: Починай одразу з контенту статті. Не додавай вступні фрази типу "Чудово", "Приступаємо", "Давайте створимо" тощо. Починай зразу з заголовка та контенту.

Цільова аудиторія: Українці, які живуть у {city} або планують там працювати/вести бізнес.

Актуальні дані з Google (використовуй для контексту):
{google_info}

Структура статті (HTML формат, використовуй h2, h3, p, ul):
1. Вступ: Ситуація на ринку {category} у {city}. Чи є попит?
2. Де шукати клієнтів/покупців (огляд місцевих сайтів оголошень {country}, групи Facebook).
3. Чому UkrFix - це найкращий новий варіант (безкоштовно, орієнтовано на своїх, зручно).
4. Покрокова інструкція: Як правильно скласти оголошення, щоб зателефонували (додай приклад тексту оголошення).
5. Висновок.

В кінці статті додай кнопку (HTML): <a href="https://ukrfix.com/add-listing/" class="btn-submit">Подати оголошення на UkrFix безкоштовно</a>

Починай одразу з HTML контенту, без будь-яких коментарів або вступних фраз.
"""
    
    try:
        # Configure Gemini API
        genai.configure(api_key=get_gemini_api_key())
        
        # Get model name from config
        model_name = get_gemini_model_name()
        model = genai.GenerativeModel(model_name)
        
        # Generate content
        response = model.generate_content(prompt)
        
        html_content = response.text
        
        # Clean up: remove AI thinking/intro phrases if they appear
        lines = html_content.split('\n')
        cleaned_lines = []
        intro_phrases_lower = [
            "чудово, приступаємо",
            "чудово, приступаємо до",
            "чудово, давайте",
            "чудово, давайте створимо",
            "приступаємо до",
            "давайте створимо",
            "починаємо створення",
            "створимо детальну",
            "ось детальна",
            "нижче наведено",
        ]
        
        skip_intro_lines = True
        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # Skip intro lines
            if skip_intro_lines:
                # Check if this line contains intro phrases
                is_intro_line = any(phrase in line_lower for phrase in intro_phrases_lower)
                
                # Also skip lines that are just "`html" or similar markers
                if line_stripped in ['`html', '```html', '```', '`']:
                    continue
                
                # Skip short intro lines (less than 50 chars and contain intro phrases)
                if is_intro_line and len(line_stripped) < 100:
                    continue
                
                # If we find HTML tags or longer content, stop skipping
                if '<' in line_stripped or len(line_stripped) > 50:
                    skip_intro_lines = False
            
            if not skip_intro_lines or len(line_stripped) > 50:
                cleaned_lines.append(line)
        
        html_content = '\n'.join(cleaned_lines)
        
        # Remove markdown code block markers if present
        html_content = html_content.strip()
        if html_content.startswith('```html'):
            html_content = html_content[7:].strip()
        elif html_content.startswith('```'):
            html_content = html_content[3:].strip()
        if html_content.endswith('```'):
            html_content = html_content[:-3].strip()
        
        return topic, html_content
    except Exception as e:
        error_msg = str(e)
        
        # Check for model not found errors (404)
        if "404" in error_msg or "not found" in error_msg.lower():
            log_error(f"Gemini API model not found: {error_msg}")
            log_error(f"Current model: {get_gemini_model_name()}")
            log_error("Please check available models at: https://ai.google.dev/models")
            log_error(f"Make sure GEMINI_MODEL is set to 'gemini-2.5-flash' in your environment variables")
        
        # Check for quota/billing errors
        if "429" in error_msg or "quota" in error_msg.lower() or "billing" in error_msg.lower():
            log_error(f"Gemini API quota/billing error: {error_msg}")
            log_error("The model may require a paid tier or quota is exceeded.")
            log_error(f"Current model: {get_gemini_model_name()}")
            log_error("Check your billing/quota at: https://ai.dev/usage?tab=rate-limit")
        
        log_error(f"Gemini API error: {e}")
        raise
