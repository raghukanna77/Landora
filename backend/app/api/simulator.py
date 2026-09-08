from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any
from ..database import get_db
from ..models.project import Project
from ..models.risk import AuditLog
from ..auth.security import get_current_user
from ..models.user import User
from ..ml.predict import predict_from_dict, predict_for_project

router = APIRouter()

class SimReq(BaseModel):
    project_id: int
    changes: Dict[str, Any]

@router.post("/counterfactual")
def counterfactual(req: SimReq, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    p=db.query(Project).filter(Project.id==req.project_id).first()
    if not p: raise HTTPException(404,"Not found")
    before = predict_for_project(p)
    # build feature dict for simulation without mutating DB
    feat={
        "affected_landowners": p.affected_landowners,
        "affected_area": p.affected_area,
        "grievances": p.grievances,
        "grievance_growth_rate": p.grievance_growth_rate,
        "compensation_pending_pct": p.compensation_pending_pct,
        "notification_age_days": p.notification_age_days,
        "document_completeness_pct": p.document_completeness_pct,
        "legal_disputes": p.legal_disputes,
        "consultation_progress_pct": p.consultation_progress_pct,
        "utility_conflicts": p.utility_conflicts,
        "land_records_match_pct": p.land_records_match_pct,
        "pending_clearances": p.pending_clearances,
        "historical_regional_delay_rate": p.historical_regional_delay_rate,
        "historical_stage_delay_rate": p.historical_stage_delay_rate,
        "stage": p.current_stage,
        "state": p.state,
        "district": p.district,
        "project_size": p.project_size,
    }
    # apply changes with validation clamp
    for k,v in req.changes.items():
        if k in feat:
            if k in ["compensation_pending_pct","document_completeness_pct","consultation_progress_pct","land_records_match_pct"]:
                feat[k]=max(0,min(100,float(v)))
            elif k in ["grievances","legal_disputes","utility_conflicts","pending_clearances","notification_age_days","affected_landowners"]:
                feat[k]=max(0,int(v))
            else:
                feat[k]=v
    prob_after, level_after = predict_from_dict(feat)
    change = prob_after - before["probability"]
    interpretation = "Risk decreases" if change<0 else "Risk increases" if change>0 else "No change"
    db.add(AuditLog(user_id=user.id, action="simulation", resource_type="project", resource_id=str(p.id), meta=str(req.changes)))
    db.commit()
    return {"success":True,"data":{"project_id":p.id,"before_probability":round(before["probability"],3),"after_probability":round(prob_after,3),"risk_change":round(change,3),"before_level":before["risk_level"],"after_level":level_after,"interpretation":interpretation,"simulation_only":True},"meta":{}}
