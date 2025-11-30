"""
Centralized logging module.
All logging should go through this module for consistent formatting.
"""


def log(*args):
    """
    Log a message with bot prefix.
    
    Args:
        *args: Variable arguments to log
    """
    print("[UKRFIX-SEO-BOT]", *args)


def log_error(*args):
    """
    Log an error message with bot prefix.
    
    Args:
        *args: Variable arguments to log
    """
    print("[UKRFIX-SEO-BOT] [ERROR]", *args)


def log_success(*args):
    """
    Log a success message with bot prefix.
    
    Args:
        *args: Variable arguments to log
    """
    print("[UKRFIX-SEO-BOT] [SUCCESS]", *args)



