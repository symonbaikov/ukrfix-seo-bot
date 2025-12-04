"""
SEO generator module - generates articles via Google Gemini API.
Returns tuple of (title, html_content).
"""

import google.generativeai as genai
from src.config import get_gemini_api_key, get_gemini_model_name
from src.utils.logger import log_error


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
    # Determine article topic based on category type
    action = "найти клиентов на"
    if "Продажа" in category or "Авто" in category:
        action = "найти покупателей на"
    if "Аренда" in category:
        action = "найти арендаторов на"
    
    topic = f"Как {action} {category} в г. {city} ({country})"
    
    prompt = f"""
Напиши детальную, полезную SEO-статью для сайта UkrFix.com.

Тема: {topic}

Целевая аудитория: Украинцы, которые живут в {city} или планируют там работать/вести бизнес.

Актуальные данные из Google (используй для контекста):
{google_info}

Структура статьи (HTML формат, используй h2, h3, p, ul):
1. Вступление: Ситуация на рынке {category} в {city}. Есть ли спрос?
2. Где искать клиентов/покупателей (обзор местных сайтов объявлений {country}, группы Facebook).
3. Почему UkrFix - это лучший новый вариант (бесплатно, ориентировано на своих, удобно).
4. Пошаговая инструкция: Как правильно составить объявление, чтобы позвонили (добавь пример текста объявления).
5. Заключение.

В конце статьи добавь кнопку (HTML): <a href="https://ukrfix.com/add-listing/" class="btn-submit">Подать объявление на UkrFix бесплатно</a>
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




