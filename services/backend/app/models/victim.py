import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from app.database import Base

class Victim(Base):
    __tablename__ = "victims"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Optional link to Supabase Auth user (set after account creation)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, unique=True)
    name_encrypted = Column(Text, nullable=False)        # AES-256 Encrypted
    contact_encrypted = Column(Text, nullable=False)     # AES-256 Encrypted
    email_encrypted = Column(Text, nullable=True)        # AES-256 Encrypted
    vulnerability_category = Column(String(50), nullable=False, default="SC/ST_PoA_Sec3")
    preferred_language = Column(String(10), nullable=False, default="hi")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
