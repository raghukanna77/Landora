from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.project import Project
from ..models.risk import RiskPrediction, ShapExplanation, AuditLog
from ..auth.security import get_current_user, can_access_project
from ..models.user import User
from ..ml.predict import predict_for_project
from ..ml.explain import explain_project

router = APIRouter()

@router.get("/projects/{pid}/risk")
def get_risk(pid:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    p=db.query(Project).filter(Project.id==pid).first()
    if not p: raise HTTPException(404,"Not found")
    if not can_access_project(user,p): raise HTTPException(403,"Forbidden")
    pred=db.query(RiskPrediction).filter(RiskPrediction.project_id==pid).order_by(RiskPrediction.prediction_timestamp.desc()).first()
    if not pred: raise HTTPException(404,"No prediction")
    exps=db.query(ShapExplanation).filter(ShapExplanation.prediction_id==pred.id).all()
    return {"success":True,"data":{"project_id":pid,"stage":pred.stage,"probability":pred.probability,"risk_level":pred.risk_level,"model_version":pred.model_version,"timestamp":pred.prediction_timestamp.isoformat(),"explanations":[{"feature":e.feature,"contribution":e.contribution,"direction":e.direction,"human_explanation":e.human_explanation} for e in exps]},"meta":{}}

@router.post("/projects/{pid}/predict")
def predict(pid:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    p=db.query(Project).filter(Project.id==pid).first()
    if not p: raise HTTPException(404,"Not found")
    if not can_access_project(user,p): raise HTTPException(403,"Forbidden")
    res=predict_for_project(p)
    pred=RiskPrediction(project_id=p.id, stage=p.current_stage, probability=res["probability"], risk_level=res["risk_level"], model_version=res["model_version"])
    db.add(pred); db.commit(); db.refresh(pred)
    exps=explain_project(p)
    for e in exps:
        db.add(ShapExplanation(prediction_id=pred.id, feature=e["feature"], contribution=e["contribution"], direction=e["direction"], human_explanation=e["human_explanation"]))
    db.add(AuditLog(user_id=user.id, action="predict", resource_type="project", resource_id=str(pid)))
    db.commit()
    return {"success":True,"data":{"project_id":pid,"stage":p.current_stage,"probability":res["probability"],"risk_level":res["risk_level"],"model_version":res["model_version"],"explanations":exps},"meta":{}}

@router.get("/projects/{pid}/explanation")
def explanation(pid:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    p=db.query(Project).filter(Project.id==pid).first()
    if not p: raise HTTPException(404,"Not found")
    exps=explain_project(p)
    return {"success":True,"data":exps,"meta":{}}
