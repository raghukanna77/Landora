from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..models.project import Project
from ..models.grievance import Grievance
from ..models.risk import AuditLog, RiskPrediction
from ..auth.security import get_current_user
from ..nlp.pipeline import analyze_grievance
from ..models.user import User

router = APIRouter()

class GrievanceCreate(BaseModel):
    project_id: int
    text: str

class AnalyzeReq(BaseModel):
    text: str

@router.post("/grievances")
def create_grievance(payload: GrievanceCreate, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    p=db.query(Project).filter(Project.id==payload.project_id).first()
    if not p: raise HTTPException(404,"Project not found")
    ana=analyze_grievance(payload.text)
    g=Grievance(project_id=payload.project_id, text=payload.text, sentiment=ana["sentiment"], intent=ana["intent"], urgency=ana["urgency"], confidence=ana["confidence"], cluster_id=ana["cluster_id"])
    db.add(g)
    # update project aggregates
    p.grievances = (p.grievances or 0)+1
    # update growth and pending? simple bump
    db.commit(); db.refresh(g)
    # optionally recalc risk?
    from ..ml.predict import predict_for_project
    from ..models.risk import RiskPrediction, ShapExplanation
    from ..ml.explain import explain_project
    res=predict_for_project(p)
    pred=RiskPrediction(project_id=p.id, stage=p.current_stage, probability=res["probability"], risk_level=res["risk_level"], model_version=res["model_version"])
    db.add(pred); db.commit()
    exps=explain_project(p)
    for e in exps:
        db.add(ShapExplanation(prediction_id=pred.id, feature=e["feature"], contribution=e["contribution"], direction=e["direction"], human_explanation=e["human_explanation"]))
    db.add(AuditLog(user_id=user.id, action="grievance_create", resource_type="project", resource_id=str(p.id), meta=ana["intent"]))
    db.commit()
    return {"success":True,"data":{"id":g.id, **ana, "risk_updated":res},"meta":{"note":"Risk updated after grievance intelligence."}}

@router.post("/grievances/analyze")
def analyze(req: AnalyzeReq, user:User=Depends(get_current_user)):
    ana=analyze_grievance(req.text)
    return {"success":True,"data":ana,"meta":{}}
@router.get("/projects/{pid}/grievances")
def list_grievances(pid:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    gs=db.query(Grievance).filter(Grievance.project_id==pid).order_by(Grievance.created_at.desc()).all()
    return {"success":True,"data":[{"id":g.id,"text":g.text,"sentiment":g.sentiment,"intent":g.intent,"urgency":g.urgency,"confidence":g.confidence,"cluster_id":g.cluster_id,"created_at":g.created_at.isoformat()} for g in gs],"meta":{}}
@router.get("/projects/{pid}/grievance-summary")
def summary(pid:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    gs=db.query(Grievance).filter(Grievance.project_id==pid).all()
    total=len(gs)
    neg=len([g for g in gs if g.sentiment=="NEGATIVE"])
    high=len([g for g in gs if g.urgency=="HIGH"])
    intents={}
    for g in gs: intents[g.intent]=intents.get(g.intent,0)+1
    top_intent=max(intents, key=lambda k: intents[k]) if intents else None
    return {"success":True,"data":{"total":total,"negative_pct": round(neg/total*100,1) if total else 0,"high_urgency":high,"top_intent":top_intent,"intent_distribution":intents},"meta":{}}
