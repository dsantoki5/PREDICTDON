import hashlib
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

# Secret key and algorithm for JWT
SECRET_KEY = "predictcnc_super_secret_jwt_key_divya_2026_industrial_ai"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

import re

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validates password complexity:
    - Min 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter (A-Z)."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter (a-z)."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit (0-9)."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+/\\\[\]`~]", password):
        return False, "Password must contain at least one special character (e.g. @, #, $, %, etc.)."
    return True, ""

def hash_password(password: str) -> str:
    """Hashes password using SHA-256 for consistent deterministic hashing."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verify_password(plain_password: str, stored_password: str) -> bool:
    """
    Verifies password against stored string.
    Supports both hashed passwords and legacy plain text fallback.
    """
    if not stored_password:
        return False
    # Check if direct match (legacy imported plaintext)
    if plain_password == stored_password:
        return True
    # Check SHA-256 hash match
    hashed = hash_password(plain_password)
    if hashed == stored_password:
        return True
    return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None
