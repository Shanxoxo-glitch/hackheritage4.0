import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from app.database import Base

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("case_files.id"), nullable=False)
    channel = Column(String(20), nullable=False) # "PWA", "SMS", "IVRS", "WEB"
    language = Column(String(10), nullable=False, default="hi")
    occurred_at = Column(DateTime, default=datetime.utcnow)
    transcript = Column(Text, nullable=True)
