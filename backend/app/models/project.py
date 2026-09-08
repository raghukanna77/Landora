from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from ..database import Base

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    project_code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    state = Column(String, nullable=False)
    district = Column(String, nullable=False)
    department = Column(String, nullable=False)
    project_type = Column(String, nullable=False)
    current_stage = Column(String, nullable=False)
    project_size = Column(String, nullable=False)
    affected_landowners = Column(Integer, nullable=False)
    affected_area = Column(Float, nullable=False)
    status = Column(String, default="ACTIVE")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geometry = Column(Text, nullable=True)  # GeoJSON string; PostGIS in prod
    # feature fields stored denormalized for fast prediction
    grievances = Column(Integer, default=0)
    grievance_growth_rate = Column(Float, default=0)
    compensation_pending_pct = Column(Float, default=0)
    notification_age_days = Column(Integer, default=0)
    document_completeness_pct = Column(Float, default=100)
    legal_disputes = Column(Integer, default=0)
    consultation_progress_pct = Column(Float, default=100)
    utility_conflicts = Column(Integer, default=0)
    land_records_match_pct = Column(Float, default=100)
    pending_clearances = Column(Integer, default=0)
    historical_regional_delay_rate = Column(Float, default=0.3)
    historical_stage_delay_rate = Column(Float, default=0.3)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AcquisitionStageRecord(Base):
    __tablename__ = "acquisition_stage_records"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=False, index=True)
    stage = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=True)
    target_date = Column(DateTime, nullable=True)
    completion_date = Column(DateTime, nullable=True)
    status = Column(String, default="PENDING")
    delay_days = Column(Integer, default=0)
    remarks = Column(Text, nullable=True)
