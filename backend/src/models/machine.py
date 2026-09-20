from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Date, DateTime
from src.database.session import Base

class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)
    machine_code = Column(String(30), unique=True, index=True, nullable=False)
    machine_name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=True)
    manufacturer = Column(String(100), nullable=True)
    installation_date = Column(Date, nullable=True)
    status = Column(String(20), default="Healthy", index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
