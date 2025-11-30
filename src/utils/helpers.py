"""
Helper utility functions.
"""

import random
from typing import Optional


def get_random_location(locations: dict) -> Optional[tuple[str, str]]:
    """
    Get a random country and city from locations dictionary.
    
    Args:
        locations: Dictionary mapping countries to lists of cities
        
    Returns:
        Tuple of (country, city) or None if locations is empty
    """
    if not locations:
        return None
    
    country = random.choice(list(locations.keys()))
    city = random.choice(locations[country])
    return country, city




