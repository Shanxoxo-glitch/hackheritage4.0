import uuid
from datetime import datetime
from sqlalchemy import Column, String, Date, DateTime, ForeignKey
from app.database import Base

class CaseFile(Base):
    __tablename__ = "case_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    victim_id = Column(String(36), ForeignKey("victims.id"), nullable=False)
    fir_number = Column(String(100), nullable=False)
    act_section = Column(String(100), nullable=False, default="SC/ST PoA Act 1989")
    case_stage = Column(String(50), nullable=False, default="FIR") # "FIR", "CHARGESHEET", "TRIAL", "COMPENSATION"
    registered_on = Column(Date, nullable=False)
    next_hearing_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
