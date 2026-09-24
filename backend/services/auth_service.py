"""
PredictCNC Authentication Service — Secure hashing, credential verification, and user management.
Uses Werkzeug PBKDF2/scrypt hashing with automatic migration for legacy SHA-256 digests.
"""
import hashlib
import hmac
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from werkzeug.security import generate_password_hash, check_password_hash
from db import query_one, query_all, execute_insert, execute_update

# Security validation constants
PASSWORD_MIN_LENGTH = 8
SPECIAL_CHARS_PATTERN = r'[!@#$%^&*(),.?":{}|<>\-_=+/\\\[\]`~]'
EMAIL_PATTERN = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
USERNAME_PATTERN = r'^[a-zA-Z0-9_.-]{3,50}$'

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Generates modern Werkzeug salted password hash (pbkdf2:sha256 or scrypt)."""
        return generate_password_hash(password)

    @classmethod
    def validate_password_complexity(cls, password: str) -> None:
        """
        Validates password meets industrial security requirements:
        - Minimum 8 characters
        - At least 1 uppercase letter (A-Z)
        - At least 1 lowercase letter (a-z)
        - At least 1 numeric digit (0-9)
        - At least 1 special character (!@#$%^&*...)
        """
        if not password or not isinstance(password, str):
            raise ValueError("Password is required.")
        if len(password) < PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long.")
        if not re.search(r'[A-Z]', password):
            raise ValueError("Password must contain at least one uppercase letter (A-Z).")
        if not re.search(r'[a-z]', password):
            raise ValueError("Password must contain at least one lowercase letter (a-z).")
        if not re.search(r'\d', password):
            raise ValueError("Password must contain at least one numeric digit (0-9).")
        if not re.search(SPECIAL_CHARS_PATTERN, password):
            raise ValueError("Password must contain at least one special character (!@#$%^&*).")

    @classmethod
    def validate_email_format(cls, email: str) -> None:
        """Validates that email conforms to standard format."""
        if not email or not isinstance(email, str):
            raise ValueError("Email address is required.")
        email_clean = email.strip()
        if len(email_clean) < 5 or len(email_clean) > 254 or not re.match(EMAIL_PATTERN, email_clean):
            raise ValueError("Please provide a valid email address (e.g. operator@company.com).")

    @classmethod
    def validate_username_format(cls, username: str) -> None:
        """Validates username length and permitted characters."""
        if not username or not isinstance(username, str):
            raise ValueError("Username is required.")
        u_clean = username.strip()
        if not re.match(USERNAME_PATTERN, u_clean):
            raise ValueError("Username must be between 3 and 50 characters and contain only letters, numbers, hyphens, underscores, or dots.")

    @classmethod
    def validate_registration_payload(
        cls,
        company_name: str,
        admin_name: str,
        email: str,
        username: str,
        password: str
    ) -> None:
        """Performs end-to-end validation on all user registration fields."""
        if not company_name or len(company_name.strip()) < 2:
            raise ValueError("Company name must be at least 2 characters long.")
        if not admin_name or len(admin_name.strip()) < 2:
            raise ValueError("Admin name must be at least 2 characters long.")
        cls.validate_username_format(username)
        cls.validate_email_format(email)
        cls.validate_password_complexity(password)

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """
        Verifies password supporting both modern Werkzeug hashes and legacy SHA-256 hex digests.
        """
        if not hashed_password or not plain_password:
            return False
            
        # 1. Try modern werkzeug hash verification
        try:
            if check_password_hash(hashed_password, plain_password):
                return True
        except Exception:
            pass

        # 2. Fallback check for legacy SHA-256 hex digests (64 hex characters)
        try:
            legacy_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
            if hmac.compare_digest(legacy_hash, hashed_password):
                return True
        except Exception:
            pass

        return False

    @classmethod
    def get_user_by_id(cls, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves user profile by primary key."""
        return query_one("SELECT * FROM users WHERE id = %s", (user_id,))

    @classmethod
    def authenticate_user(
        cls,
        username_or_email: str,
        password: str,
        company_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Authenticates user against users table. Supports username or email (with optional company disambiguation)."""
        if not username_or_email or not password:
            return None
        ident = username_or_email.strip()
        if not ident or not password.strip():
            return None

        if company_name and company_name.strip():
            users = query_all(
                "SELECT * FROM users WHERE (LOWER(username) = LOWER(%s) OR LOWER(email) = LOWER(%s)) AND LOWER(company_name) = LOWER(%s) ORDER BY (id = 1) DESC, id ASC",
                (ident, ident, company_name.strip())
            )
        else:
            users = query_all(
                "SELECT * FROM users WHERE LOWER(username) = LOWER(%s) OR LOWER(email) = LOWER(%s) ORDER BY (id = 1) DESC, (LOWER(username) = LOWER(%s)) DESC, id ASC",
                (ident, ident, ident)
            )
        
        if not users:
            return None
        
        for user in users:
            stored_hash = user["password"]
            if cls.verify_password(password, stored_hash):
                # Transparently upgrade legacy SHA-256 hashes to modern werkzeug hashes
                if not stored_hash.startswith("scrypt:") and not stored_hash.startswith("pbkdf2:"):
                    new_hash = cls.hash_password(password)
                    try:
                        execute_update("UPDATE users SET password = %s WHERE id = %s", (new_hash, user["id"]))
                        user["password"] = new_hash
                    except Exception:
                        pass
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
        """Registers a new company administrator/user. Validates all inputs and enforces uniqueness."""
        cls.validate_registration_payload(company_name, admin_name, email, username, password)

        existing = query_one(
            "SELECT id FROM users WHERE LOWER(username) = LOWER(%s)",
            (username.strip(),)
        )
        if existing:
            raise ValueError(f"Username '{username.strip()}' is already taken. Please choose a different username.")

        hashed_pwd = cls.hash_password(password)
        return execute_insert(
            """INSERT INTO users (company_name, admin_name, email, username, password, role, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (company_name.strip(), admin_name.strip(), email.strip(), username.strip(), hashed_pwd, role, datetime.now())
        )

    @classmethod
    def change_password(cls, user_id: int, current_password: str, new_password: str) -> bool:
        """
        Securely changes user password requiring current password verification and complexity validation.
        """
        user = cls.get_user_by_id(user_id)
        if not user:
            raise ValueError("User account not found.")

        if not cls.verify_password(current_password, user["password"]):
            raise ValueError("Current password is incorrect.")

        cls.validate_password_complexity(new_password)

        new_hash = cls.hash_password(new_password)
        execute_update("UPDATE users SET password = %s WHERE id = %s", (new_hash, user_id))
        return True

    @classmethod
    def reset_password(cls, identifier: str, new_password: str, company_name: Optional[str] = None) -> bool:
        """Resets user password by username or email with company scoping and complexity validation."""
        if not identifier or not identifier.strip():
            raise ValueError("Username or email address is required.")

        cls.validate_password_complexity(new_password)
        ident = identifier.strip()

        if company_name and company_name.strip():
            user = query_one(
                "SELECT * FROM users WHERE (LOWER(username) = LOWER(%s) OR LOWER(email) = LOWER(%s)) AND LOWER(company_name) = LOWER(%s)",
                (ident, ident, company_name.strip())
            )
        else:
            user = query_one("SELECT * FROM users WHERE LOWER(username) = LOWER(%s)", (ident,))
            if not user:
                users_by_email = query_all("SELECT * FROM users WHERE LOWER(email) = LOWER(%s)", (ident,))
                if len(users_by_email) == 1:
                    user = users_by_email[0]
                elif len(users_by_email) > 1:
                    raise ValueError("Multiple companies are registered under this email. Please enter your Username or Company Name to specify which account to reset.")

        if not user:
            raise ValueError("No account found with the provided username or email address.")
            
        hashed_pwd = cls.hash_password(new_password)
        execute_update("UPDATE users SET password = %s WHERE id = %s", (hashed_pwd, user["id"]))
        return True



