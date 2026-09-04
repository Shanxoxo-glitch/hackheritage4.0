import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey
from app.database import Base

class DistressScore(Base):
    __tablename__ = "distress_scores"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    interaction_id = Column(String(36), ForeignKey("interactions.id"), nullable=False)
    sentiment_score = Column(Float, nullable=False, default=0.0)
    voice_stress_score = Column(Float, nullable=False, default=0.0)
    threat_flag = Column(Boolean, nullable=False, default=False)
    composite_score = Column(Float, nullable=False, default=0.0)
    confidence = Column(Float, nullable=False, default=0.95)
    trend_flag = Column(String(20), nullable=False, default="STABLE") # "IMPROVING", "STABLE", "ESCALATING"
    created_at = Column(DateTime, default=datetime.utcnow)
