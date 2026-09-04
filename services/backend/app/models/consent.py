import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from app.database import Base

class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    victim_id = Column(String(36), ForeignKey("victims.id"), nullable=False)
    scope = Column(String(100), nullable=False)  # e.g., "SMS_CHECKIN", "LOCATION_SHARING", "SAFE_PAUSE"
    status = Column(String(20), nullable=False, default="GRANTED") # "GRANTED", "REVOKED", "PAUSED"
    granted_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
