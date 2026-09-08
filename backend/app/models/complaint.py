from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from datetime import datetime
from ..database import Base
import secrets

class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(String, unique=True, index=True, nullable=False)  # BD-2026-PB-004821
    project_name = Column(String, nullable=False)
    project_id = Column(Integer, nullable=True, index=True)
    state = Column(String, nullable=False)
    district = Column(String, nullable=False)
    village = Column(String, nullable=True)
    category = Column(String, nullable=False)  # Compensation, Land Record, etc.
    details = Column(Text, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    # contact
    contact_preference = Column(String, default="anonymous")  # with_contact / anonymous
    name = Column(String, nullable=True)
    mobile = Column(String, nullable=True)
    email = Column(String, nullable=True)
    # NLP
    intent = Column(String, nullable=True)
    sentiment = Column(String, nullable=True)
    urgency = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    stage_mapped = Column(String, nullable=True)
    # workflow
    status = Column(String, default="Submitted")  # Submitted, AI Classified, Officer Review, Action Assigned, In Progress, Resolved
    assigned_department = Column(String, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def generate_complaint_id(state_code="XX"):
    # BD-2026-XX-XXXXXX
    year = datetime.utcnow().year
    num = secrets.randbelow(900000) + 100000
    # use random but deterministic for demo? secrets is ok
    sc = (state_code[:2].upper() if state_code else "XX").ljust(2,"X")
    return f"BD-{year}-{sc}-{num:06d}"
