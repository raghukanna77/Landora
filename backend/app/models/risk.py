from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from ..database import Base

class RiskPrediction(Base):
    __tablename__ = "risk_predictions"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    stage = Column(String, nullable=False)
    probability = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    feature_version = Column(String, default="v1")
    prediction_timestamp = Column(DateTime, default=datetime.utcnow)

class ShapExplanation(Base):
    __tablename__ = "shap_explanations"
    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("risk_predictions.id"), nullable=False)
    feature = Column(String, nullable=False)
    contribution = Column(Float, nullable=False)
    direction = Column(String, nullable=False)
    human_explanation = Column(String, nullable=False)

class PrecedentMatch(Base):
    __tablename__ = "precedent_matches"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=False, index=True)
    reference_project_id = Column(Integer, nullable=False)
    similarity = Column(Float, nullable=False)
    spatial_distance = Column(Float, nullable=True)
    pattern = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    stage = Column(String, nullable=False)
    action = Column(String, nullable=False)
    owner_role = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    predicted_risk_reduction = Column(Float, nullable=True)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)

class Outcome(Base):
    __tablename__ = "outcomes"
    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    accepted = Column(String, nullable=True)
    action_taken = Column(String, nullable=True)
    result = Column(String, nullable=True)
    outcome_label = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ModelRun(Base):
    __tablename__ = "model_runs"
    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String, nullable=False)
    dataset_version = Column(String, nullable=False)
    training_time = Column(DateTime, default=datetime.utcnow)
    roc_auc = Column(Float, nullable=True)
    pr_auc = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1 = Column(Float, nullable=True)
    calibration_error = Column(Float, nullable=True)
    approved = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=True)
    recipient_id = Column(Integer, nullable=True)
    type = Column(String, nullable=False)
    message = Column(String, nullable=False)
    status = Column(String, default="UNREAD")
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=True)
    resource_id = Column(String, nullable=True)
    meta = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
