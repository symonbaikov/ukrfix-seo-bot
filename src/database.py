"""
Database module - handles all SQLite operations.
Only this module communicates with history.db.
"""

import sqlite3
from typing import Optional
from src.utils.logger import log_error


DB_PATH = "history.db"


def init_db() -> None:
    """
    Initialize database and create posted table if it doesn't exist.
    Should be called at bot startup.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS posted
                     (country text, city text, category text,
                      UNIQUE(country, city, category))''')
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        log_error(f"Database initialization failed: {e}")
        raise


def is_posted(country: str, city: str, category: str) -> bool:
    """
    Check if a combination of country, city, category was already posted.
    
    Args:
        country: Country name
        city: City name
        category: Category name
        
    Returns:
        True if combination exists, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT * FROM posted WHERE country=? AND city=? AND category=?",
            (country, city, category)
        )
        result = c.fetchone() is not None
        conn.close()
        return result
    except sqlite3.Error as e:
        log_error(f"Database query failed: {e}")
        raise


def mark_posted(country: str, city: str, category: str) -> None:
    """
    Mark a combination as posted in the database.
    
    Args:
        country: Country name
        city: City name
        category: Category name
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO posted VALUES (?, ?, ?)",
            (country, city, category)
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        log_error(f"Database insert failed: {e}")
        raise




