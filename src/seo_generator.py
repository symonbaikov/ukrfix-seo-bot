"""
SEO generator module - generates articles via OpenAI API.
Returns tuple of (title, html_content).
"""

from openai import OpenAI
from src.config import get_openai_api_key
from src.utils.logger import log_error


def generate_article(country: str, city: str, category: str, google_info: str) -> tuple[str, str]:
    """
    Generate SEO article using OpenAI API.
    
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
        client = OpenAI(api_key=get_openai_api_key())
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        
        html_content = response.choices[0].message.content
        return topic, html_content
    except Exception as e:
        log_error(f"OpenAI API error: {e}")
        raise



