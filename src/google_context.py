"""
Google context module - collects context from Google search.
Returns text that will be used in OpenAI prompt.
"""

from typing import Optional
from googlesearch import search
from src.utils.logger import log_error


def get_google_context(query: str) -> str:
    """
    Search Google for relevant information and return context text.
    
    Args:
        query: Search query string
        
    Returns:
        Context text with search results descriptions
    """
    try:
        results = []
        for url in search(query, num_results=3, advanced=True):
            results.append(f"- {url.title}: {url.description}")
        
        if results:
            return "\n".join(results)
        else:
            return "Информация не найдена."
    except Exception as e:
        log_error(f"Google search failed: {e}")
        return "Информация не найдена."



