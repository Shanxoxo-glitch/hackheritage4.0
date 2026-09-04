import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from app.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    score_id = Column(String(36), ForeignKey("distress_scores.id"), nullable=False)
    official_id = Column(String(36), nullable=True) # ID of assigned official/counsellor
    risk_level = Column(String(20), nullable=False) # "LOW", "MODERATE", "HIGH", "CRITICAL"
    raised_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(30), default="PENDING") # "PENDING", "ASSIGNED", "ACKNOWLEDGED", "RESOLVED"
    confirmed_outcome = Column(String(30), nullable=True) # "TRUE_POSITIVE", "FALSE_POSITIVE", "UNCLEAR"

    # Cryptographic SHA-256 Audit Chain
    previous_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False)
