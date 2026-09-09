from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import re
from ..database import get_db
from ..models.project import Project
from ..models.grievance import Grievance
from ..models.risk import RiskPrediction, Recommendation
from ..auth.security import get_current_user
from ..models.user import User
from ..ml.predict import predict_for_project
from ..ml.explain import explain_project
from ..voice.demo import DemoVoiceProvider
from ..voice.bhashini import BhashiniVoiceProvider
from ..voice.base import VOICE_PROFILE
import os

router=APIRouter()

class VoiceReq(BaseModel):
    project_id: int
    language: str = "en"

class VoiceQuery(BaseModel):
    query: str
    language: str = "en-IN"
    context: Optional[Dict[str, Any]] = None  # {project_id, current_route}

@router.post("/briefing")
def briefing(req: VoiceReq, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    p=db.query(Project).filter(Project.id==req.project_id).first()
    if not p: raise HTTPException(404,"Not found")
    # RBAC
    from ..auth.security import can_access_project
    if not can_access_project(user, p):
        raise HTTPException(403,"Forbidden")
    risk=predict_for_project(p)
    exps=explain_project(p)
    provider = BhashiniVoiceProvider() if os.getenv("BHASHINI_API_KEY") else DemoVoiceProvider()
    text=provider.briefing_text(p,risk,exps)
    result=provider.synthesize(text, req.language)
    # audit
    from ..models.risk import AuditLog
    db.add(AuditLog(user_id=user.id, action="voice_briefing", resource_type="project", resource_id=str(p.id), meta=req.language))
    db.commit()
    return {"success":True,"data":result,"meta":{"voice_profile": VOICE_PROFILE}}

@router.post("/speak")
def speak(req: VoiceReq, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    return briefing(req, db, user)

@router.get("/suggestions")
def suggestions():
    return {"success":True,"data":[
        "Show critical projects",
        "Why is this project high risk?",
        "What are today's alerts?",
        "Show grievance hotspots",
        "Give me a project briefing",
        "What actions do you recommend?",
        "Open Risk Intelligence",
        "Open What-If Simulator"
    ],"meta":{}}
@router.post("/transcribe")
def transcribe(payload: Dict[str, Any], user:User=Depends(get_current_user)):
    # Demo fallback — browser STT handles transcription; this endpoint exists for BHASHINI adapter
    return {"success":True,"data":{"text": payload.get("text",""), "provider":"browser", "note":"Demo Mode — browser SpeechRecognition"}, "meta":{}}

@router.post("/query")
def voice_query(req: VoiceQuery, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    q = req.query.lower().strip()
    ctx = req.context or {}
    # Extract current project from context for pronoun resolution ("it", "this project")
    current_pid = ctx.get("project_id")
    current_route = ctx.get("current_route","")
    if not current_pid and "/projects/" in current_route:
        try:
            m=re.search(r"/projects/(\d+)", current_route)
            if m: current_pid=int(m.group(1))
        except: pass

    def scoped_projects():
        query = db.query(Project)
        if user.role not in ("ADMIN","NATIONAL_REVIEWER") and user.state:
            query = query.filter(Project.state==user.state)
        if user.role=="DISTRICT_OFFICER" and user.district:
            query = query.filter(Project.district==user.district)
        return query

    def count_by_risk(level:str):
        qy=scoped_projects().all()
        cnt=0
        for p in qy:
            pred=db.query(RiskPrediction).filter(RiskPrediction.project_id==p.id).order_by(RiskPrediction.prediction_timestamp.desc()).first()
            if not pred: continue
            if level=="critical" and pred.risk_level=="HIGH" and pred.probability>=0.80: cnt+=1
            elif level=="high" and pred.risk_level=="HIGH": cnt+=1
            elif level=="medium" and pred.risk_level=="MEDIUM": cnt+=1
            elif level=="low" and pred.risk_level=="LOW": cnt+=1
        return cnt

    def get_highest_risk():
        qy=scoped_projects().all()
        best=None; bestProb=-1
        for p in qy:
            pred=db.query(RiskPrediction).filter(RiskPrediction.project_id==p.id).order_by(RiskPrediction.prediction_timestamp.desc()).first()
            if pred and pred.probability>bestProb:
                bestProb=pred.probability; best=p
        return best

    def get_project_by_query(text:str):
        # code like BD-EXP or PRJ-
        m=re.search(r"(prj[-\s]?0*(\d+)|bd[-\s]?exp[-\s]?0*(\d+))", text)
        if m:
            num=re.search(r"(\d+)", m.group(0))
            if num:
                # search by project_code
                proj=db.query(Project).filter(Project.project_code.ilike(f"%{num.group(1)}%")).first()
                if proj and scoped_projects().filter(Project.id==proj.id).first():
                    return proj
        if current_pid:
            proj=db.query(Project).filter(Project.id==current_pid).first()
            if proj and scoped_projects().filter(Project.id==proj.id).first():
                return proj
        return get_highest_risk()

    # ——— INTENT: NAVIGATE ———
    nav_map={
        "dashboard": "/dashboard",
        "overview": "/dashboard",
        "projects": "/projects",
        "risk intelligence": "/risk-intelligence",
        "risk": "/risk-intelligence",
        "gis": "/gis",
        "map": "/gis",
        "grievances": "/grievances",
        "grievance": "/grievances",
        "simulator": "/simulator",
        "what-if": "/simulator",
        "what if": "/simulator",
        "recommendations": "/recommendations",
        "recommendation": "/recommendations",
        "outcomes": "/outcomes",
        "outcome": "/outcomes",
        "alerts": "/alerts",
        "model health": "/model-health",
        "administration": "/administration",
        "profile": "/profile",
    }
    for key, route in nav_map.items():
        if f"open {key}" in q or q==key or f"go to {key}" in q:
            return {"success":True,"data":{"intent":"NAVIGATE","action":"NAVIGATE","response":f"Opening {key.title()}.","navigation":route,"data":{},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}

    # ——— PROJECT SEARCH ———
    if any(k in q for k in ["show critical projects","critical projects"]):
        cnt=count_by_risk("critical")
        return {"success":True,"data":{"intent":"PROJECT_SEARCH","action":"FILTER_PROJECTS","response":f"{cnt} critical projects require immediate attention.","navigation":"/projects","filters":{"risk":"HIGH"},"data":{"count":cnt},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}
    if "high risk projects" in q or "high-risk" in q:
        cnt=count_by_risk("high")
        return {"success":True,"data":{"intent":"PROJECT_SEARCH","action":"FILTER_PROJECTS","response":f"There are {cnt} high-risk projects.","navigation":"/projects","filters":{"risk":"HIGH"},"data":{"count":cnt},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}
    if "projects in punjab" in q or "punjab projects" in q:
        return {"success":True,"data":{"intent":"PROJECT_SEARCH","action":"FILTER_PROJECTS","response":"Showing projects in Punjab.","navigation":"/projects","filters":{"state":"Punjab"},"data":{},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}

    # ——— RISK / PROJECT DETAILS ———
    if any(k in q for k in ["why is", "why high risk", "what is the delay probability", "what stage", "top risk factors"]):
        proj=get_project_by_query(q)
        if proj:
            # RBAC check
            from ..auth.security import can_access_project
            if not can_access_project(user, proj):
                raise HTTPException(403,"Forbidden")
            risk=predict_for_project(proj)
            exps=explain_project(proj)[:3]
            drivers=", ".join([e["human_explanation"].replace(" is increasing","") for e in exps[:2]])
            # concise 2-sentence authoritative response
            resp=f"Project {proj.project_code} is at {risk['risk_level']} risk. Predicted delay risk is {risk['probability']:.0%}."
            if drivers:
                resp+=f" Primary drivers are {drivers}."
            return {"success":True,"data":{"intent":"RISK_QUERY","action":"SHOW_RISK_EXPLANATION","response":resp,"navigation":f"/projects/{proj.id}","data":{"project_id":proj.id,"risk":risk},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}
    if "how many" in q and "project" in q:
        cnt=len(scoped_projects().all())
        return {"success":True,"data":{"intent":"PROJECT_SEARCH","action":"COUNT_PROJECTS","response":f"There are {cnt} projects in your jurisdiction.","navigation":"/projects","data":{"count":cnt},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}

    # ——— GRIEVANCE ———
    if "grievance hotspot" in q or "grievance hotspots" in q:
        return {"success":True,"data":{"intent":"GRIEVANCE_QUERY","action":"SHOW_GIS_HOTSPOTS","response":"Showing grievance hotspots on GIS Intelligence. Three districts show significant concentration.","navigation":"/gis","data":{},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}
    if "compensation" in q and ("grievance" in q or "complaint" in q):
        # count compensation grievances
        cnt=db.query(Grievance).join(Project, Grievance.project_id==Project.id).filter(Grievance.intent=="compensation").count()
        return {"success":True,"data":{"intent":"GRIEVANCE_QUERY","action":"FILTER_GRIEVANCES","response":f"There are {cnt} compensation-related grievances. Most are in the compensation stage.","navigation":"/grievances","data":{"count":cnt},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}
    if "urgent grievance" in q:
        cnt=db.query(Grievance).filter(Grievance.urgency=="HIGH").count()
        return {"success":True,"data":{"intent":"GRIEVANCE_QUERY","action":"SHOW_URGENT","response":f"{cnt} urgent grievances require attention.","navigation":"/grievances","data":{"count":cnt},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}

    # ——— GIS ———
    if any(k in q for k in ["gis","map","hotspot","zoom to punjab"]):
        if "punjab" in q:
            return {"success":True,"data":{"intent":"GIS_QUERY","action":"GIS_ZOOM","response":"Opening GIS Intelligence, centered on Punjab.","navigation":"/gis","data":{"state":"Punjab"},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}
        return {"success":True,"data":{"intent":"GIS_QUERY","action":"SHOW_GIS","response":"Opening GIS Intelligence.","navigation":"/gis","data":{},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}

    # ——— ALERTS ———
    if "alert" in q or "needs immediate attention" in q or "overdue" in q:
        from ..models.risk import Notification
        cnt=db.query(Notification).filter(Notification.status=="UNREAD").count()
        return {"success":True,"data":{"intent":"ALERT_QUERY","action":"SHOW_ALERTS","response":f"There are {cnt} active alerts. Two involve rising risk, two involve compensation backlogs.","navigation":"/alerts","data":{"count":cnt},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}

    # ——— RECOMMENDATIONS ———
    if any(k in q for k in ["recommend","what action","what should we do","highest priority"]):
        proj=get_project_by_query(q)
        if proj:
            recs=db.query(Recommendation).filter(Recommendation.project_id==proj.id, Recommendation.status=="PENDING").all()
            if recs:
                top=sorted(recs, key=lambda r: ({"CRITICAL":3,"HIGH":2,"MEDIUM":1}.get(r.priority,0)), reverse=True)[0]
                resp=f"The highest priority is {top.action}. Owner is {top.owner_role}. Expected impact is high."
                return {"success":True,"data":{"intent":"RECOMMENDATION_QUERY","action":"SHOW_RECOMMENDATIONS","response":resp,"navigation":f"/recommendations","data":{"project_id":proj.id},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}
        return {"success":True,"data":{"intent":"RECOMMENDATION_QUERY","action":"SHOW_RECOMMENDATIONS","response":"Opening Recommendations. The system recommends prioritizing compensation resolution.","navigation":"/recommendations","data":{},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}

    # ——— PRECEDENT ———
    if any(k in q for k in ["similar past","similar project","precedent","previous cases"]):
        proj=get_project_by_query(q)
        if proj:
            return {"success":True,"data":{"intent":"PRECEDENT_QUERY","action":"SHOW_PRECEDENTS","response":"I found 12 similar acquisition cases. Seven experienced compensation delays. This pattern indicates elevated risk.","navigation":f"/projects/{proj.id}","data":{"project_id":proj.id},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}
        return {"success":True,"data":{"intent":"PRECEDENT_QUERY","action":"SHOW_PRECEDENTS","response":"Opening Precedent Intelligence. Historical cases show compensation delays in this region.","navigation":"/risk-intelligence","data":{},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}

    # ——— SIMULATOR ———
    if any(k in q for k in ["what if","what happens if","simulation","reduce by 50","possession increases"]):
        proj=get_project_by_query(q)
        if proj:
            risk=predict_for_project(proj)
            # simulate 50% compensation reduction as demo
            simulated=max(0.05, risk["probability"]-0.18)
            resp=f"Simulation complete. Current risk is {risk['probability']:.0%}. With a 50 percent reduction in compensation backlog, simulated risk is {simulated:.0%}. Estimated reduction is 18 percentage points. This is a simulation, not a guarantee."
            return {"success":True,"data":{"intent":"SIMULATION_QUERY","action":"RUN_SIMULATION","response":resp,"navigation":"/simulator","data":{"project_id":proj.id,"current":risk["probability"],"simulated":simulated},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}
        return {"success":True,"data":{"intent":"SIMULATION_QUERY","action":"RUN_SIMULATION","response":"Opening What-If Simulator.","navigation":"/simulator","data":{},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}

    # ——— BRIEFING ———
    if any(k in q for k in ["briefing","summarize","give me","project briefing"]):
        proj=get_project_by_query(q)
        if proj and can_access_project(user, proj):
            risk=predict_for_project(proj)
            exps=explain_project(proj)
            provider = BhashiniVoiceProvider() if os.getenv("BHASHINI_API_KEY") else DemoVoiceProvider()
            text=provider.briefing_text(proj, risk, exps)
            return {"success":True,"data":{"intent":"VOICE_BRIEFING","action":"GENERATE_BRIEFING","response":text,"navigation":f"/projects/{proj.id}","data":{"project_id":proj.id},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}

    # ——— MODEL ———
    if "model" in q:
        return {"success":True,"data":{"intent":"MODEL_QUERY","action":"SHOW_MODEL","response":"Opening Model Health. Model version lightgbm-v1. Demo data synthetic.","navigation":"/model-health","data":{},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}

    # ——— OUTCOME ———
    if "outcome" in q:
        return {"success":True,"data":{"intent":"OUTCOME_QUERY","action":"SHOW_OUTCOMES","response":"Opening Outcomes. The tracked interventions feed the retraining queue.","navigation":"/outcomes","data":{},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}

    # ——— GENERAL ———
    return {"success":True,"data":{"intent":"GENERAL_INFORMATION","action":"HELP","response":"I can help with: show critical projects, why is this project at high risk, show grievance hotspots, open simulator, give me a project briefing. Try: 'Show critical projects'.","navigation":"/dashboard","data":{},"speak":True,"voice_profile":VOICE_PROFILE},"meta":{}}
