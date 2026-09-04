import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from app.database import Base

class Intervention(Base):
    __tablename__ = "interventions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id = Column(String(36), ForeignKey("alerts.id"), nullable=False)
    official_id = Column(String(36), nullable=False)
    intervention_type = Column(String(50), nullable=False) # "counselling", "legal", "medical", "relocation", "protection", "financial"
    status = Column(String(30), default="SCHEDULED") # "SCHEDULED", "IN_PROGRESS", "COMPLETED"
    scheduled_on = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
