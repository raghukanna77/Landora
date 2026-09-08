from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from datetime import datetime
from ..database import Base

class Grievance(Base):
    __tablename__ = "grievances"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    sentiment = Column(String, nullable=True)
    intent = Column(String, nullable=True)
    urgency = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    cluster_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
