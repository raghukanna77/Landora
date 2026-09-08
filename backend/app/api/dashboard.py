from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.project import Project
from ..models.risk import RiskPrediction, Notification, ModelRun
from ..models.grievance import Grievance
from ..auth.security import get_current_user
from ..models.user import User
from ..config import settings
from sqlalchemy import func

router = APIRouter()

def risk_level(prob): 
    if prob < settings.RISK_THRESHOLD_LOW: return "LOW"
    if prob < settings.RISK_THRESHOLD_HIGH: return "MEDIUM"
    return "HIGH"

@router.get("/summary")
def summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(Project)
    if user.role not in ("ADMIN","NATIONAL_REVIEWER"):
        if user.state: q=q.filter(Project.state==user.state)
    projects = q.all()
    total=len(projects)
    # get latest predictions per project
    high=med=low=0
    alerts=0
    risk_sum=0
    for p in projects:
        pred=db.query(RiskPrediction).filter(RiskPrediction.project_id==p.id).order_by(RiskPrediction.prediction_timestamp.desc()).first()
        if pred:
            risk_sum+=pred.probability
            if pred.risk_level=="HIGH": high+=1
            elif pred.risk_level=="MEDIUM": med+=1
            else: low+=1
            if pred.probability>=settings.RISK_THRESHOLD_HIGH: alerts+=1
    avg = risk_sum/total if total else 0
    mr=db.query(ModelRun).order_by(ModelRun.created_at.desc()).first()
    return {"success":True,"data":{"total_projects":total,"high_risk":high,"medium_risk":med,"low_risk":low,"average_risk":round(avg,3),"early_alerts":alerts,"model_health": {"version": mr.model_version if mr else "lightgbm-v1", "roc_auc": mr.roc_auc if mr else 0.85}},"meta":{}}

@router.get("/stage-risk")
def stage_risk(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stages=["Notification","SIA","Consent","Award","Compensation","Possession"]
    out=[]
    for s in stages:
        q=db.query(Project).filter(Project.current_stage==s)
        if user.role not in ("ADMIN","NATIONAL_REVIEWER") and user.state:
            q=q.filter(Project.state==user.state)
        projs=q.all()
        if not projs: 
            out.append({"stage":s,"project_count":0,"average_risk":0,"high_risk_count":0}); continue
        probs=[]
        high=0
        for p in projs:
            pred=db.query(RiskPrediction).filter(RiskPrediction.project_id==p.id).order_by(RiskPrediction.prediction_timestamp.desc()).first()
            if pred:
                probs.append(pred.probability)
                if pred.risk_level=="HIGH": high+=1
        avg=sum(probs)/len(probs) if probs else 0
        out.append({"stage":s,"project_count":len(projs),"average_risk":round(avg,3),"high_risk_count":high})
    return {"success":True,"data":out,"meta":{}}
@router.get("/state-risk")
def state_risk(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    states=db.query(Project.state).distinct().all()
    out=[]
    for (st,) in states:
        projs=db.query(Project).filter(Project.state==st).all()
        probs=[]
        for p in projs:
            pred=db.query(RiskPrediction).filter(RiskPrediction.project_id==p.id).order_by(RiskPrediction.prediction_timestamp.desc()).first()
            if pred: probs.append(pred.probability)
        avg=sum(probs)/len(probs) if probs else 0
        out.append({"state":st,"project_count":len(projs),"average_risk":round(avg,3)})
    return {"success":True,"data":out,"meta":{}}
@router.get("/heatmap")
def heatmap(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q=db.query(Project)
    if user.role not in ("ADMIN","NATIONAL_REVIEWER") and user.state:
        q=q.filter(Project.state==user.state)
    projs=q.all()
    data=[]
    for p in projs:
        pred=db.query(RiskPrediction).filter(RiskPrediction.project_id==p.id).order_by(RiskPrediction.prediction_timestamp.desc()).first()
        if pred and p.latitude and p.longitude:
            data.append({"project_id":p.id,"name":p.name,"lat":p.latitude,"lon":p.longitude,"risk_level":pred.risk_level,"probability":pred.probability,"stage":p.current_stage})
    return {"success":True,"data":data,"meta":{}}
@router.get("/alerts")
def alerts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    notifs=db.query(Notification).order_by(Notification.created_at.desc()).limit(20).all()
    # also generate risk increase alerts on fly
    data=[{"id":n.id,"project_id":n.project_id,"type":n.type,"message":n.message,"status":n.status,"created_at":n.created_at.isoformat() if n.created_at else None} for n in notifs]
    return {"success":True,"data":data,"meta":{}}
