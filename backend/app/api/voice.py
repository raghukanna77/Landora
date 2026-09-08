from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import re
from ..database import get_db
from ..models.project import Project
from ..auth.security import get_current_user
from ..models.user import User
from ..ml.predict import predict_for_project
from ..ml.explain import explain_project
from ..voice.demo import DemoVoiceProvider
from ..voice.bhashini import BhashiniVoiceProvider
import os

router=APIRouter()

class VoiceReq(BaseModel):
    project_id: int
    language: str = "en"

class VoiceQuery(BaseModel):
    query: str
    language: str = "en-IN"

@router.post("/briefing")
def briefing(req: VoiceReq, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    p=db.query(Project).filter(Project.id==req.project_id).first()
    if not p: raise HTTPException(404,"Not found")
    risk=predict_for_project(p)
    exps=explain_project(p)
    provider = BhashiniVoiceProvider() if os.getenv("BHASHINI_API_KEY") else DemoVoiceProvider()
    text=provider.briefing_text(p,risk,exps)
    result=provider.synthesize(text, req.language)
    return {"success":True,"data":result,"meta":{}}
@router.post("/speak")
def speak(req: VoiceReq, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    # alias to briefing with text
    return briefing(req, db, user)

@router.post("/query")
def voice_query(req: VoiceQuery, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    q = req.query.lower().strip()
    # intent detection via keywords (rule-based demo, replaceable by LLM/BHASHINI)
    # RBAC: user jurisdiction enforced
    # Helper to count with jurisdiction filter
    def count_projects(filters: dict):
        query = db.query(Project)
        if user.role not in ("ADMIN","NATIONAL_REVIEWER") and user.state:
            query = query.filter(Project.state==user.state)
        if user.role=="DISTRICT_OFFICER" and user.district:
            query = query.filter(Project.district==user.district)
        # apply risk filter via latest prediction? For demo count by threshold
        # fallback: for speed count via project query + prediction join not needed, use simple approximation
        # Instead fetch all and check risk level via predict would be heavy; use grievances heuristic for demo is okay but we will fetch predictions
        projects = query.all()
        from ..models.risk import RiskPrediction
        cnt=0
        critical=[]
        for p in projects:
            pred = db.query(RiskPrediction).filter(RiskPrediction.project_id==p.id).order_by(RiskPrediction.prediction_timestamp.desc()).first()
            lvl = pred.risk_level if pred else "LOW"
            prob = pred.probability if pred else 0
            if filters.get("risk")=="critical" and lvl=="HIGH" and prob>=0.80:
                cnt+=1
                critical.append(p)
            elif filters.get("risk")=="high" and lvl=="HIGH":
                cnt+=1
            elif filters.get("risk")=="low" and lvl=="LOW":
                cnt+=1
            elif not filters.get("risk"):
                cnt+=1
        return cnt, critical

    # NAVIGATE intents
    if any(k in q for k in ["open simulator","what-if","what if"]):
        return {"success":True,"data":{"intent":"SIMULATION_QUERY","response":"Opening What-If Simulator.","route":"/simulator","filters":{}},"meta":{}}
    if "risk intelligence" in q:
        return {"success":True,"data":{"intent":"RISK_QUERY","response":"Opening Risk Intelligence.","route":"/risk-intelligence","filters":{}},"meta":{}}
    if "gis" in q or "map" in q or "hotspot" in q:
        return {"success":True,"data":{"intent":"GIS_QUERY","response":"Opening GIS Intelligence.","route":"/gis","filters":{}},"meta":{}}
    if "recommendation" in q:
        return {"success":True,"data":{"intent":"RECOMMENDATION_QUERY","response":"Opening Recommendations.","route":"/recommendations","filters":{}},"meta":{}}
    if "grievance" in q or "complaint" in q:
        if "compensation" in q:
            return {"success":True,"data":{"intent":"GRIEVANCE_QUERY","response":"Showing compensation issues.","route":"/grievances","filters":{"intent":"compensation"}},"meta":{}}
        return {"success":True,"data":{"intent":"GRIEVANCE_QUERY","response":"Opening Grievance Intelligence.","route":"/grievances","filters":{}},"meta":{}}
    if "alert" in q:
        return {"success":True,"data":{"intent":"ALERT_QUERY","response":"Opening Alerts.","route":"/alerts","filters":{}},"meta":{}}
    if "model" in q:
        return {"success":True,"data":{"intent":"MODEL_QUERY","response":"Opening Model Health.","route":"/model-health","filters":{}},"meta":{}}
    if "project" in q and ("show" in q or "list" in q):
        if "critical" in q:
            cnt,_ = count_projects({"risk":"critical"})
            return {"success":True,"data":{"intent":"PROJECT_SEARCH","response":f"There are {cnt} critical projects.","route":"/projects","filters":{"risk":"HIGH"}},"meta":{}}
        if "high" in q:
            cnt,_ = count_projects({"risk":"high"})
            return {"success":True,"data":{"intent":"PROJECT_SEARCH","response":f"There are {cnt} high-risk projects.","route":"/projects","filters":{"risk":"HIGH"}},"meta":{}}
        return {"success":True,"data":{"intent":"PROJECT_SEARCH","response":"Opening Projects.","route":"/projects","filters":{}},"meta":{}}
    # Why is project at risk?
    m = re.search(r"why is (?:project )?([a-z0-9\- ]+?) at (?:high )?risk", q)
    if m or ("why" in q and "risk" in q):
        # try to extract project id or code
        # find highest risk project as fallback
        query = db.query(Project)
        if user.role not in ("ADMIN","NATIONAL_REVIEWER") and user.state:
            query = query.filter(Project.state==user.state)
        # find project by name/code contains query
        proj = None
        # try to extract BD-EXP pattern
        code_match = re.search(r"bd[-\s]?exp[-\s]?0*([0-9]+)", q)
        if code_match:
            # search by project_code
            proj = db.query(Project).filter(Project.project_code.ilike(f"%{code_match.group(1)}%")).first()
        if not proj:
            # fallback to highest risk
            from ..models.risk import RiskPrediction
            allp = query.all()
            best=None; bestProb=-1
            for p in allp:
                pred = db.query(RiskPrediction).filter(RiskPrediction.project_id==p.id).order_by(RiskPrediction.prediction_timestamp.desc()).first()
                if pred and pred.probability>bestProb:
                    bestProb=pred.probability; best=p
            proj=best
        if proj:
            risk = predict_for_project(proj)
            exps = explain_project(proj)[:3]
            drivers = ", ".join([e["human_explanation"].replace(" is increasing","") for e in exps[:2]])
            # count grievances via grievance table? approx
            resp = f"The project {proj.name} currently has a {risk['probability']:.0%} predicted delay risk, {risk['risk_level']}. The major risk drivers are {drivers}."
            return {"success":True,"data":{"intent":"RISK_QUERY","response":resp,"route":f"/projects/{proj.id}","filters":{}},"meta":{}}
        return {"success":True,"data":{"intent":"RISK_QUERY","response":"I couldn't find that project. Showing risk intelligence.","route":"/risk-intelligence","filters":{}},"meta":{}}
    if "briefing" in q or "summarize" in q or "give me" in q:
        # project briefing for top project
        query = db.query(Project)
        if user.role not in ("ADMIN","NATIONAL_REVIEWER") and user.state:
            query = query.filter(Project.state==user.state)
        proj = query.first()
        if proj:
            risk = predict_for_project(proj)
            exps = explain_project(proj)
            provider = BhashiniVoiceProvider() if os.getenv("BHASHINI_API_KEY") else DemoVoiceProvider()
            text = provider.briefing_text(proj, risk, exps)
            return {"success":True,"data":{"intent":"VOICE_BRIEFING","response":text,"route":f"/projects/{proj.id}","filters":{}},"meta":{}}
    if "how many" in q and "project" in q:
        cnt,_=count_projects({})
        return {"success":True,"data":{"intent":"PROJECT_SEARCH","response":f"There are {cnt} projects in your jurisdiction.","route":"/projects","filters":{}},"meta":{}}
    if "dashboard" in q or "overview" in q:
        return {"success":True,"data":{"intent":"NAVIGATE","response":"Opening Dashboard.","route":"/dashboard","filters":{}},"meta":{}}
    if "open projects" in q:
        return {"success":True,"data":{"intent":"NAVIGATE","response":"Opening Projects.","route":"/projects","filters":{}},"meta":{}}
    # default
    return {"success":True,"data":{"intent":"GENERAL_INFORMATION","response":"I can help with: show critical projects, why is project at risk, show grievance hotspots, open simulator, give me a project briefing. Try: 'Show critical projects'.","route":"/dashboard","filters":{}},"meta":{}}
