from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.project import Project
from ..models.risk import RiskPrediction
from ..auth.security import get_current_user, can_access_project
from ..models.user import User
from pydantic import BaseModel

router = APIRouter()

class ProjectCreate(BaseModel):
    project_code: str
    name: str
    description: Optional[str]=None
    state: str
    district: str
    department: str
    project_type: str
    current_stage: str
    project_size: str
    affected_landowners: int
    affected_area: float
    latitude: Optional[float]=None
    longitude: Optional[float]=None
    grievances: int=0
    compensation_pending_pct: float=0
    notification_age_days: int=0
    document_completeness_pct: float=100
    legal_disputes: int=0
    consultation_progress_pct: float=100
    utility_conflicts: int=0
    land_records_match_pct: float=100
    pending_clearances: int=0
    grievance_growth_rate: float=0
    historical_regional_delay_rate: float=0.3
    historical_stage_delay_rate: float=0.3

@router.get("")
def list_projects(search: Optional[str]=None, state: Optional[str]=None, district: Optional[str]=None, stage: Optional[str]=None, risk: Optional[str]=None, sort: Optional[str]=None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q=db.query(Project)
    if user.role not in ("ADMIN","NATIONAL_REVIEWER") and user.state:
        q=q.filter(Project.state==user.state)
        if user.role=="DISTRICT_OFFICER" and user.district:
            q=q.filter(Project.district==user.district)
    if search:
        q=q.filter((Project.name.ilike(f"%{search}%")) | (Project.project_code.ilike(f"%{search}%")))
    if state: q=q.filter(Project.state==state)
    if district: q=q.filter(Project.district==district)
    if stage and stage!="ALL": q=q.filter(Project.current_stage==stage)
    projs=q.all()
    # attach risk
    enriched=[]
    for p in projs:
        pred=db.query(RiskPrediction).filter(RiskPrediction.project_id==p.id).order_by(RiskPrediction.prediction_timestamp.desc()).first()
        prob=pred.probability if pred else 0
        level=pred.risk_level if pred else "LOW"
        if risk and risk!="ALL" and level!=risk: continue
        enriched.append({"id":p.id,"project_code":p.project_code,"name":p.name,"state":p.state,"district":p.district,"department":p.department,"current_stage":p.current_stage,"project_size":p.project_size,"affected_landowners":p.affected_landowners,"latitude":p.latitude,"longitude":p.longitude,"probability":prob,"risk_level":level,"updated_at":p.updated_at.isoformat() if p.updated_at else None})
    if sort=="highest_risk": enriched.sort(key=lambda x: x["probability"], reverse=True)
    elif sort=="lowest_risk": enriched.sort(key=lambda x: x["probability"])
    elif sort=="newest": enriched.sort(key=lambda x: x["id"], reverse=True)
    return {"success":True,"data":enriched,"meta":{"count":len(enriched)}}

@router.post("")
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if db.query(Project).filter(Project.project_code==payload.project_code).first():
        raise HTTPException(400, "Duplicate project_code")
    p=Project(**payload.model_dump())
    db.add(p); db.commit(); db.refresh(p)
    # generate prediction
    from ..ml.predict import predict_for_project
    from ..models.risk import RiskPrediction, AuditLog
    res=predict_for_project(p)
    rp=RiskPrediction(project_id=p.id, stage=p.current_stage, probability=res["probability"], risk_level=res["risk_level"], model_version=res["model_version"])
    db.add(rp); db.add(AuditLog(user_id=user.id, action="create_project", resource_type="project", resource_id=str(p.id))); db.commit()
    return {"success":True,"data":{"id":p.id,"project_code":p.project_code},"meta":{}}
@router.get("/{pid}")
def get_project(pid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p=db.query(Project).filter(Project.id==pid).first()
    if not p: raise HTTPException(404,"Not found")
    if not can_access_project(user,p): raise HTTPException(403,"Forbidden")
    pred=db.query(RiskPrediction).filter(RiskPrediction.project_id==p.id).order_by(RiskPrediction.prediction_timestamp.desc()).first()
    return {"success":True,"data":{"id":p.id,"project_code":p.project_code,"name":p.name,"description":p.description,"state":p.state,"district":p.district,"department":p.department,"project_type":p.project_type,"current_stage":p.current_stage,"project_size":p.project_size,"affected_landowners":p.affected_landowners,"affected_area":p.affected_area,"status":p.status,"latitude":p.latitude,"longitude":p.longitude,"grievances":p.grievances,"grievance_growth_rate":p.grievance_growth_rate,"compensation_pending_pct":p.compensation_pending_pct,"notification_age_days":p.notification_age_days,"document_completeness_pct":p.document_completeness_pct,"legal_disputes":p.legal_disputes,"consultation_progress_pct":p.consultation_progress_pct,"utility_conflicts":p.utility_conflicts,"land_records_match_pct":p.land_records_match_pct,"pending_clearances":p.pending_clearances,"historical_regional_delay_rate":p.historical_regional_delay_rate,"historical_stage_delay_rate":p.historical_stage_delay_rate,"risk":{"probability":pred.probability if pred else None,"risk_level":pred.risk_level if pred else None,"model_version":pred.model_version if pred else None,"timestamp":pred.prediction_timestamp.isoformat() if pred else None}},"meta":{}}

@router.put("/{pid}")
def update_project(pid: int, payload: ProjectCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p=db.query(Project).filter(Project.id==pid).first()
    if not p: raise HTTPException(404,"Not found")
    for k,v in payload.model_dump().items(): setattr(p,k,v)
    db.commit(); db.refresh(p)
    return {"success":True,"data":{"id":p.id},"meta":{}}
