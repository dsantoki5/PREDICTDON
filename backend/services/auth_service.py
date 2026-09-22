"""
PredictCNC Authentication Service — Secure hashing, credential verification, and user management.
"""
import hashlib
import hmac
from datetime import datetime
from typing import Optional, Dict, Any
from db import query_one, execute_insert

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Generates SHA-256 hex digest for password storage."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """Verifies password using constant-time comparison."""
        computed_hash = cls.hash_password(plain_password)
        return hmac.compare_digest(computed_hash, hashed_password)

    @classmethod
    def authenticate_user(cls, username_or_email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticates user against users table."""
        user = query_one(
            "SELECT * FROM users WHERE username = %s OR email = %s",
            (username_or_email.strip(), username_or_email.strip())
        )
        if not user:
            return None
        
        # Check password hash
        stored_hash = user["password"]
        if cls.verify_password(password, stored_hash):
            return user
        return None

    @classmethod
    def register_user(
        cls,
        company_name: str,
        admin_name: str,
        email: str,
        username: str,
        password: str,
        role: str = "Administrator"
    ) -> int:
        """Registers a new company administrator/user."""
        existing = query_one(
            "SELECT id FROM users WHERE username = %s OR email = %s",
            (username.strip(), email.strip())
        )
        if existing:
            raise ValueError("Username or Email already registered in system.")

        hashed_pwd = cls.hash_password(password)
        return execute_insert(
            """INSERT INTO users (company_name, admin_name, email, username, password, role, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (company_name.strip(), admin_name.strip(), email.strip(), username.strip(), hashed_pwd, role, datetime.now())
        )

    @classmethod
    def reset_password(cls, identifier: str, new_password: str, company_name: Optional[str] = None) -> bool:
        """Resets user password by username or email."""
        from db import execute_update
        user = query_one(
            "SELECT * FROM users WHERE username = %s OR email = %s",
            (identifier.strip(), identifier.strip())
        )
        if not user:
            raise ValueError("No account found with the provided username or email address.")
        hashed_pwd = cls.hash_password(new_password)
        execute_update("UPDATE users SET password = %s WHERE id = %s", (hashed_pwd, user["id"]))
        return True

