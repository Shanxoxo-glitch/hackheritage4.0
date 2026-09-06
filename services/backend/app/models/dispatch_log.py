import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from app.database import Base

class DispatchLog(Base):
    __tablename__ = "dispatch_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), nullable=False, index=True)
    tier = Column(String(20), nullable=False)
    action = Column(String(100), nullable=False)
    dispatched_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
