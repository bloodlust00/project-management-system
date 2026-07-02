import re
from app.exceptions.custom import BadRequestException

def validate_password_strength(password: str) -> str:
    """Verifies that the password meets security strength requirements."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("Password must contain at least one special character.")
    return password

def sanitize_string(value: str) -> str:
    """Sanitizes input strings by stripping away potential HTML/Javascript tags to prevent XSS."""
    if not value:
        return value
    # Simple regex block to strip html tags
    clean = re.compile("<.*?>")
    return re.sub(clean, "", value).strip()
