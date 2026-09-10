import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    supabase_uid = Column(String(255), unique=True, nullable=True) # Maps to Supabase auth.users.id
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(20), nullable=False, default="victim") # victim | counselor | admin
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
