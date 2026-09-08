from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..models.risk import Outcome, Recommendation, RiskPrediction
from ..models.project import Project
from ..auth.security import get_current_user
from ..models.user import User
from ..models.risk import AuditLog

router=APIRouter()

class OutcomeCreate(BaseModel):
    recommendation_id: Optional[int]=None
    project_id: int
    accepted: str
    action_taken: str
    result: str
    outcome_label: str

@router.post("/outcomes")
def create_outcome(payload: OutcomeCreate, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    o=Outcome(**payload.model_dump())
    db.add(o); db.commit(); db.refresh(o)
    db.add(AuditLog(user_id=user.id, action="outcome_create", resource_type="project", resource_id=str(payload.project_id)))
    # optional: create notification for retraining queue implicitly
    db.commit()
    return {"success":True,"data":{"id":o.id},"meta":{}}
@router.get("/projects/{pid}/outcomes")
def list_outcomes(pid:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    rows=db.query(Outcome).filter(Outcome.project_id==pid).order_by(Outcome.created_at.desc()).all()
    return {"success":True,"data":[{"id":r.id,"recommendation_id":r.recommendation_id,"project_id":r.project_id,"accepted":r.accepted,"action_taken":r.action_taken,"result":r.result,"outcome_label":r.outcome_label,"created_at":r.created_at.isoformat()} for r in rows],"meta":{}}
@router.get("/outcomes")
def all_outcomes(db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    rows=db.query(Outcome).order_by(Outcome.created_at.desc()).limit(50).all()
    return {"success":True,"data":[{"id":r.id,"project_id":r.project_id,"outcome_label":r.outcome_label,"created_at":r.created_at.isoformat()} for r in rows],"meta":{}}
