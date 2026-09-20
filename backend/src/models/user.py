from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from src.database.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(150), nullable=False, index=True)
    admin_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    username = Column(String(50), nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(String(50), default="Administrator")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
