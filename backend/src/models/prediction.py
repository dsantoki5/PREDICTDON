from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Numeric, DateTime, ForeignKey
from src.database.session import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False, index=True)
    air_temperature = Column(Float, nullable=False)
    process_temperature = Column(Float, nullable=False)
    rotational_speed = Column(Float, nullable=False)
    torque = Column(Float, nullable=False)
    tool_wear = Column(Float, nullable=False)
    load_density = Column(Float, nullable=True)
    rpm_torque_interaction = Column(Float, nullable=True)
    temperature_difference = Column(Float, nullable=True)
    temperature_ratio = Column(Float, nullable=True)
    load_stress = Column(Float, nullable=True)
    tool_wear_mean_10 = Column(Float, nullable=True)
    air_temp_mean_10 = Column(Float, nullable=True)
    prediction = Column(String(50), nullable=False)
    probability = Column(Float, nullable=False)
    healthy_probability = Column(Float, nullable=True)
    warning_probability = Column(Float, nullable=True)
    critical_probability = Column(Float, nullable=True)
    confidence = Column(Numeric(5, 2), nullable=True)
    process_temp_mean_10 = Column(Float, nullable=True)
    rpm_std_10 = Column(Float, nullable=True)
    predicted_class = Column(Integer, nullable=True, default=0)
    model_version = Column(String(100), nullable=True, default="LightGBM_No_SMOTE_Final v4.2")
    predicted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
