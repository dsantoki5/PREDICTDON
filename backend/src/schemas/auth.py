from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from src.core.security import validate_password_strength

class LoginRequest(BaseModel):
    company_name: Optional[str] = None
    username: str
    password: str

class RegisterRequest(BaseModel):
    company_name: str
    admin_name: str
    email: str
    username: str
    password: str
    role: Optional[str] = "Administrator"

    @field_validator("email")
    @classmethod
    def check_email_format(cls, v: str) -> str:
        import re
        email = v.strip().lower()
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, email):
            raise ValueError("Please provide a valid email address (e.g. user@company.com).")
        
        # Check domain typos
        domain = email.split("@")[-1]
        typo_domains = {
            "gamil.com": "gmail.com",
            "gmial.com": "gmail.com",
            "gmai.com": "gmail.com",
            "gmaill.com": "gmail.com",
            "gmil.com": "gmail.com",
            "gmaik.com": "gmail.com",
            "yaho.com": "yahoo.com",
            "yahooo.com": "yahoo.com",
            "hotmial.com": "hotmail.com",
            "hotmale.com": "hotmail.com",
            "outlok.com": "outlook.com",
            "outloo.com": "outlook.com",
            "redifmail.com": "rediffmail.com",
        }
        if domain in typo_domains:
            suggestion = typo_domains[domain]
            raise ValueError(f"Invalid domain '{domain}'. Did you mean '@{suggestion}'?")

        # Check TLD
        tld = domain.split(".")[-1]
        if len(tld) < 2 or not tld.isalpha():
            raise ValueError("Email must end with a valid domain extension (e.g. .com, .org, .in, .edu).")

        return email

    @field_validator("password")
    @classmethod
    def check_password_complexity(cls, v: str) -> str:
        valid, msg = validate_password_strength(v)
        if not valid:
            raise ValueError(msg)
        return v

class UserResponse(BaseModel):
    id: int
    company_name: str
    admin_name: str
    email: str
    username: str
    role: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
