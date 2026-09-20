from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from src.database.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(100), nullable=False, index=True)
    admin_name = Column(String(100), nullable=True)
    email = Column(String(150), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="Administrator")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
