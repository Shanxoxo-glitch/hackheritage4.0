import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from app.database import Base

class Counselor(Base):
    __tablename__ = "counselors"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    specialization = Column(String(100), nullable=False, default="Victim Trauma & Legal Support")
    organization = Column(String(100), nullable=False, default="DLSA Legal Aid")
    assigned_cases_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
