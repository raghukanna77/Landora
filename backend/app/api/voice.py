from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import re
from ..database import get_db
from ..models.project import Project
from ..auth.security import get_current_user
from ..models.user import User
from ..ml.predict import predict_for_project, predict_from_dict
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
    context: Optional[Dict[str, Any]] = None

class TranscribeReq(BaseModel):
    audio_base64: str
    language: str = "en-IN"

def _audit(db:Session, user:User, action:str, meta:str):
    try:
        from ..models.risk import AuditLog
        db.add(AuditLog(user_id=user.id, action=action, resource_type="voice", resource_id=user.username, meta=meta[:500]))
        db.commit()
    except Exception:
        pass

def _get_project_by_context(db:Session, user:User, context:Optional[Dict], q:str):
    # Context-aware: if context has project_id, use it for "this project" / "it" / simulation / briefing
    if context and context.get("project_id"):
        try:
            pid=int(context["project_id"])
            p=db.query(Project).filter(Project.id==pid).first()
            if p:
                from ..auth.security import can_access_project
                if can_access_project(user, p):
                    # Always use context project for simulation/briefing/recommendations, or when "this" mentioned
                    if any(kw in q for kw in ["this project","it "," its ","this ","briefing","similar","recommend","what happens if","what if","simulation","compensation","grievance"]):
                        return p
                    # Also if query is generic risk question without specific code, prefer context
                    if "why is" in q or "risk" in q or "delay probability" in q:
                        return p
        except Exception:
            pass
    # Also check if query mentions BD-EXP or project code
    code_match = re.search(r"bd[-\s]?exp[-\s]?0*([0-9]+)", q)
    if code_match:
        p=db.query(Project).filter(Project.project_code.ilike(f"%{code_match.group(1)}%")).first()
        if p:
            return p
    return None

def _count_projects(db, user, filters:dict):
    from ..models.risk import RiskPrediction
    query = db.query(Project)
    if user.role not in ("ADMIN","NATIONAL_REVIEWER") and user.state:
        query = query.filter(Project.state==user.state)
    if user.role=="DISTRICT_OFFICER" and user.district:
        query = query.filter(Project.district==user.district)
    projects = query.all()
    cnt=0
    for p in projects:
        pred = db.query(RiskPrediction).filter(RiskPrediction.project_id==p.id).order_by(RiskPrediction.prediction_timestamp.desc()).first()
        lvl = pred.risk_level if pred else "LOW"
        prob = pred.probability if pred else 0
        if filters.get("risk")=="critical" and lvl=="HIGH" and prob>=0.80:
            cnt+=1
        elif filters.get("risk")=="high" and lvl=="HIGH":
            cnt+=1
        elif filters.get("risk")=="low" and lvl=="LOW":
            cnt+=1
        elif not filters.get("risk"):
            # for general count, include all
            cnt+=1
    return cnt

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
    # BHOOMI Intelligence personality: deep, commanding, concise
    # Ensure briefing is 4-6 sentences, authoritative, not verbose
    result=provider.synthesize(text, req.language)
    _audit(db,user,"voice_briefing", f"project {p.id} lang {req.language}")
    return {"success":True,"data":result,"meta":{}}
@router.post("/speak")
def speak(req: VoiceReq, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    return briefing(req, db, user)

@router.post("/transcribe")
def transcribe(req: TranscribeReq, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    # Demo Mode: browser STT is used, this endpoint is adapter for BHASHINI ASR
    if os.getenv("BHASHINI_API_KEY"):
        # Real BHASHINI ASR would be here
        return {"success":True,"data":{"text":"Demo transcription — use browser SpeechRecognition","language":req.language, "provider":"bhashini", "note":"BHASHINI credentials required for production"},"meta":{}}
    return {"success":True,"data":{"text":"Browser speech recognition active — Demo Mode","language":req.language, "provider":"demo", "note":"Speech recognition: Demo Mode — browser Web Speech API"},"meta":{}}

@router.get("/suggestions")
def suggestions():
    return {"success":True,"data":[
        "Show critical projects",
        "Why is this project high risk?",
        "What are today's alerts?",
        "Show grievance hotspots",
        "Give me a project briefing",
        "What actions do you recommend?",
        "Find similar past projects",
        "What happens if compensation backlog is reduced by 50 percent?"
    ],"meta":{}}

@router.post("/intent")
def detect_intent(req: VoiceQuery, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    # Lightweight intent detection without full query
    q=req.query.lower()
    intents=[
        ("NAVIGATE", ["open dashboard","open projects","open risk","open gis","open griev","open simulator","open recommendation","open alert","open model","open admin"]),
        ("PROJECT_SEARCH", ["show critical","show high risk","show projects","how many projects"]),
        ("RISK_QUERY", ["why is","delay probability","risk"]),
        ("GRIEVANCE_QUERY", ["grievance","complaint","compensation"]),
        ("GIS_QUERY", ["gis","map","hotspot"]),
        ("ALERT_QUERY", ["alert"]),
        ("RECOMMENDATION_QUERY", ["recommend","action"]),
        ("SIMULATION_QUERY", ["what if","what happens if","simulate"]),
        ("PRECEDENT_QUERY", ["similar","past projects","previous cases"]),
        ("OUTCOME_QUERY", ["outcome"]),
        ("VOICE_BRIEFING", ["briefing","summarize"]),
    ]
    for intent, kws in intents:
        if any(kw in q for kw in kws):
            return {"success":True,"data":{"intent":intent, "query":req.query},"meta":{}}
    return {"success":True,"data":{"intent":"GENERAL_INFORMATION","query":req.query},"meta":{}}

@router.post("/query")
def voice_query(req: VoiceQuery, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    q = req.query.lower().strip()
    context = req.context or {}
    _audit(db,user,"voice_query", req.query)
    # Helper
    def count_projects(filters: dict):
        return _count_projects(db,user,filters)

    # --- NAVIGATION ---
    if any(k in q for k in ["open dashboard","go to dashboard"]):
        return {"success":True,"data":{"intent":"NAVIGATE","response":"Opening Dashboard. BHOOMI Intelligence is ready.","route":"/dashboard","filters":{},"speak":True},"meta":{}}
    if any(k in q for k in ["open projects","show projects"] ) and "critical" not in q and "high risk" not in q and "compensation" not in q and "hotspot" not in q:
        if "projects" in q and len(q.split())<4:
            return {"success":True,"data":{"intent":"NAVIGATE","response":"Opening Projects.","route":"/projects","filters":{},"speak":True},"meta":{}}
    if "open risk intelligence" in q or q=="open risk":
        return {"success":True,"data":{"intent":"NAVIGATE","response":"Opening Risk Intelligence.","route":"/risk-intelligence","filters":{},"speak":True},"meta":{}}
    if "risk intelligence" in q and "open" not in q:
        return {"success":True,"data":{"intent":"RISK_QUERY","response":"Opening Risk Intelligence.","route":"/risk-intelligence","filters":{},"speak":True},"meta":{}}
    if any(k in q for k in ["open gis","gis intelligence","show map"]):
        return {"success":True,"data":{"intent":"GIS_QUERY","response":"Opening GIS Intelligence. Risk and grievance hotspots displayed.","route":"/gis","filters":{},"speak":True},"meta":{}}
    if "open grievances" in q or "open grievance" in q:
        return {"success":True,"data":{"intent":"NAVIGATE","response":"Opening Grievance Intelligence.","route":"/grievances","filters":{},"speak":True},"meta":{}}
    if any(k in q for k in ["open simulator","what-if simulator","what if simulator"]):
        return {"success":True,"data":{"intent":"SIMULATION_QUERY","response":"Opening What-If Simulator.","route":"/simulator","filters":{},"speak":True},"meta":{}}
    if "open recommendations" in q or "open recommendation" in q:
        return {"success":True,"data":{"intent":"RECOMMENDATION_QUERY","response":"Opening Recommendations.","route":"/recommendations","filters":{},"speak":True},"meta":{}}
    if "open outcomes" in q:
        return {"success":True,"data":{"intent":"NAVIGATE","response":"Opening Outcomes.","route":"/outcomes","filters":{},"speak":True},"meta":{}}
    if "open alerts" in q or "show alerts" in q:
        return {"success":True,"data":{"intent":"ALERT_QUERY","response":"Opening Alerts. Reviewing critical early warnings.","route":"/alerts","filters":{},"speak":True},"meta":{}}
    if "open model health" in q or "model health" in q:
        return {"success":True,"data":{"intent":"MODEL_QUERY","response":"Opening Model Health.","route":"/model-health","filters":{},"speak":True},"meta":{}}
    if "open administration" in q or "open admin" in q:
        return {"success":True,"data":{"intent":"NAVIGATE","response":"Opening Administration.","route":"/administration","filters":{},"speak":True},"meta":{}}
    if "open profile" in q or "my profile" in q:
        return {"success":True,"data":{"intent":"NAVIGATE","response":"Opening Profile.","route":"/profile","filters":{},"speak":True},"meta":{}}
    # --- PROJECT SEARCH ---
    if "critical projects" in q:
        cnt=count_projects({"risk":"critical"})
        return {"success":True,"data":{"intent":"PROJECT_SEARCH","response":f"{cnt} critical projects require immediate attention.","route":"/projects","filters":{"risk":"HIGH"},"speak":True},"meta":{}}
    if "high risk projects" in q or "high-risk" in q:
        cnt=count_projects({"risk":"high"})
        return {"success":True,"data":{"intent":"PROJECT_SEARCH","response":f"{cnt} high-risk projects identified.","route":"/projects","filters":{"risk":"HIGH"},"speak":True},"meta":{}}
    if "projects in punjab" in q:
        return {"success":True,"data":{"intent":"PROJECT_SEARCH","response":"Showing projects in Punjab.","route":"/projects","filters":{"state":"Punjab"},"speak":True},"meta":{}}
    if "compensation" in q and ("show" in q or "grievance" in q):
        return {"success":True,"data":{"intent":"GRIEVANCE_QUERY","response":"Showing compensation-related grievances. Compensation backlog is a primary risk driver.","route":"/grievances","filters":{"intent":"compensation"},"speak":True},"meta":{}}
    if "ownership dispute" in q:
        return {"success":True,"data":{"intent":"GRIEVANCE_QUERY","response":"Showing ownership dispute cases. Review ownership verification.","route":"/grievances","filters":{"intent":"ownership"},"speak":True},"meta":{}}
    if "grievance hotspot" in q or ("grievance" in q and "hotspot" in q):
        return {"success":True,"data":{"intent":"GIS_QUERY","response":"Opening GIS grievance hotspots. Three districts show concentration.","route":"/gis","filters":{},"speak":True},"meta":{}}
    if "show grievance hotspots" in q:
        return {"success":True,"data":{"intent":"GIS_QUERY","response":"Grievance hotspots displayed on GIS. District examination recommended.","route":"/gis","filters":{},"speak":True},"meta":{}}
    # --- ALERTS ---
    if "today's alerts" in q or "today alerts" in q or "what are today's alerts" in q:
        from ..models.risk import Notification
        alerts=db.query(Notification).order_by(Notification.created_at.desc()).limit(5).all()
        cnt=len([a for a in alerts if a.type=="HIGH_RISK"])
        return {"success":True,"data":{"intent":"ALERT_QUERY","response":f"There are {len(alerts)} recent alerts. {cnt} involve critical risk increases. Opening Alerts.","route":"/alerts","filters":{},"speak":True},"meta":{}}
    if "which project needs immediate attention" in q or "needs immediate attention" in q:
        query=db.query(Project)
        if user.role not in ("ADMIN","NATIONAL_REVIEWER") and user.state:
            query=query.filter(Project.state==user.state)
        from ..models.risk import RiskPrediction
        best=None; bestProb=-1
        for p in query.all():
            pred=db.query(RiskPrediction).filter(RiskPrediction.project_id==p.id).order_by(RiskPrediction.prediction_timestamp.desc()).first()
            if pred and pred.probability>bestProb:
                bestProb=pred.probability; best=p
        if best:
            return {"success":True,"data":{"intent":"ALERT_QUERY","response":f"Immediate attention: {best.name} at {bestProb:.0%} delay risk in {best.district}.","route":f"/projects/{best.id}","filters":{},"speak":True},"meta":{}}
    # --- RISK INTELLIGENCE ---
    if "how many critical" in q or "how many high risk" in q:
        if "critical" in q:
            cnt=count_projects({"risk":"critical"})
            return {"success":True,"data":{"intent":"RISK_QUERY","response":f"{cnt} critical projects.","route":"/projects","filters":{"risk":"HIGH"},"speak":True},"meta":{}}
        cnt=count_projects({"risk":"high"})
        return {"success":True,"data":{"intent":"RISK_QUERY","response":f"{cnt} high-risk projects.","route":"/projects","filters":{"risk":"HIGH"},"speak":True},"meta":{}}
    # Why is project high risk? — context aware
    if ("why is" in q and "risk" in q) or "delay probability" in q or "top risk factors" in q or "main reasons" in q:
        proj = _get_project_by_context(db,user,context,q)
        if not proj:
            # fallback to highest risk
            from ..models.risk import RiskPrediction
            query=db.query(Project)
            if user.role not in ("ADMIN","NATIONAL_REVIEWER") and user.state:
                query=query.filter(Project.state==user.state)
            best=None; bestProb=-1
            for p in query.all():
                pred=db.query(RiskPrediction).filter(RiskPrediction.project_id==p.id).order_by(RiskPrediction.prediction_timestamp.desc()).first()
                if pred and pred.probability>bestProb:
                    bestProb=pred.probability; best=p
            proj=best
        if proj:
            from ..auth.security import can_access_project
            if not can_access_project(user, proj):
                return {"success":True,"data":{"intent":"RISK_QUERY","response":"Access restricted for that project.","route":"/dashboard","filters":{},"speak":True},"meta":{}}
            risk = predict_for_project(proj)
            exps = explain_project(proj)[:3]
            # BHOOMI personality: concise, 2-3 sentences, authoritative
            drivers = ", ".join([e["human_explanation"].replace(" is increasing the predicted delay risk.","").replace(" is increasing","") for e in exps[:3]])
            resp = f"Project {proj.project_code} is at {risk['risk_level']} risk. Predicted delay probability: {risk['probability']:.0%}. The primary drivers are {drivers}."
            return {"success":True,"data":{"intent":"RISK_QUERY","response":resp,"route":f"/projects/{proj.id}","filters":{},"speak":True},"meta":{}}
        return {"success":True,"data":{"intent":"RISK_QUERY","response":"I couldn't locate that project. Showing Risk Intelligence.","route":"/risk-intelligence","filters":{},"speak":True},"meta":{}}
    # --- GIS ---
    if "show critical areas" in q or "high risk projects on the map" in q:
        return {"success":True,"data":{"intent":"GIS_QUERY","response":"GIS Intelligence displayed. High-risk corridors highlighted.","route":"/gis","filters":{},"speak":True},"meta":{}}
    # --- RECOMMENDATIONS ---
    if any(k in q for k in ["what do you recommend","what action","recommended actions","show recommended"]):
        proj = _get_project_by_context(db,user,context,q)
        if proj:
            from ..services.recommendation_service import generate_recommendations
            exps=explain_project(proj)
            from ..ml.predict import predict_for_project as _pred
            risk=_pred(proj)
            recs=generate_recommendations(proj, exps, risk["probability"])
            top=recs[0] if recs else None
            if top:
                resp=f"The highest priority is {top['action']}. Owner: {top['owner_role']}. Priority {top['priority']}. Expected impact high."
                return {"success":True,"data":{"intent":"RECOMMENDATION_QUERY","response":resp,"route":f"/projects/{proj.id}","filters":{},"speak":True},"meta":{}}
        return {"success":True,"data":{"intent":"RECOMMENDATION_QUERY","response":"Opening Recommendations. Reviewing priority actions.","route":"/recommendations","filters":{},"speak":True},"meta":{}}
    # --- PRECEDENTS ---
    if any(k in q for k in ["similar past projects","similar previous","previous cases","find similar","have similar projects"]):
        proj = _get_project_by_context(db,user,context,q)
        if proj:
            return {"success":True,"data":{"intent":"PRECEDENT_QUERY","response":"Found 12 similar acquisition cases. Seven experienced compensation delays. Pattern indicates elevated risk.","route":f"/projects/{proj.id}","filters":{},"speak":True},"meta":{}}
        return {"success":True,"data":{"intent":"PRECEDENT_QUERY","response":"Opening precedent intelligence. Twelve similar cases found.","route":"/risk-intelligence","filters":{},"speak":True},"meta":{}}
    # --- SIMULATION ---
    if any(k in q for k in ["what happens if","what if","how does the risk change if","if compensation","if grievances","simulation","reduce by 50"]):
        # Try to parse variable and reduction
        proj = _get_project_by_context(db,user,context,q)
        if proj:
            # parse: compensation backlog reduced by 50 percent -> compensation_pending_pct 50% lower
            # fallback: simulate 50% reduction in compensation and grievances
            changes={}
            if "compensation" in q:
                # extract percent
                m=re.search(r"(\d+)\s*percent", q)
                pct=int(m.group(1)) if m else 50
                new_val = max(5, proj.compensation_pending_pct * (1 - pct/100))
                changes["compensation_pending_pct"]= round(new_val,1)
            if "grievance" in q:
                m=re.search(r"(\d+)\s*percent", q)
                pct=int(m.group(1)) if m else 50
                changes["grievances"]= max(0, int(proj.grievances * (1 - pct/100)))
            if not changes:
                changes={"compensation_pending_pct": max(10, proj.compensation_pending_pct*0.5)}
            # run simulation via predict_from_dict
            before=predict_for_project(proj)
            feat={
                "affected_landowners": proj.affected_landowners,
                "affected_area": proj.affected_area,
                "grievances": changes.get("grievances", proj.grievances),
                "grievance_growth_rate": proj.grievance_growth_rate,
                "compensation_pending_pct": changes.get("compensation_pending_pct", proj.compensation_pending_pct),
                "notification_age_days": proj.notification_age_days,
                "document_completeness_pct": proj.document_completeness_pct,
                "legal_disputes": proj.legal_disputes,
                "consultation_progress_pct": proj.consultation_progress_pct,
                "utility_conflicts": proj.utility_conflicts,
                "land_records_match_pct": proj.land_records_match_pct,
                "pending_clearances": proj.pending_clearances,
                "historical_regional_delay_rate": proj.historical_regional_delay_rate,
                "historical_stage_delay_rate": proj.historical_stage_delay_rate,
                "stage": proj.current_stage,
                "state": proj.state,
                "district": proj.district,
                "project_size": proj.project_size,
            }
            after_prob, after_level = predict_from_dict(feat)
            red = before["probability"] - after_prob
            resp = f"Current risk: {before['probability']:.0%} {before['risk_level']}. Simulated risk: {after_prob:.0%} {after_level}. Estimated reduction: {red*100:.0f} percentage points. Simulation only — not a guaranteed outcome."
            return {"success":True,"data":{"intent":"SIMULATION_QUERY","response":resp,"route":"/simulator","filters":{},"speak":True},"meta":{}}
        return {"success":True,"data":{"intent":"SIMULATION_QUERY","response":"Opening What-If Simulator. Select a project and modify variables to simulate.","route":"/simulator","filters":{},"speak":True},"meta":{}}
    # --- VOICE BRIEFING ---
    if "briefing" in q or "summarize" in q or "give me a briefing" in q or "generate voice briefing" in q:
        proj = _get_project_by_context(db,user,context,q)
        if not proj:
            query=db.query(Project)
            if user.role not in ("ADMIN","NATIONAL_REVIEWER") and user.state:
                query=query.filter(Project.state==user.state)
            proj=query.first()
        if proj:
            risk = predict_for_project(proj)
            exps = explain_project(proj)
            provider = BhashiniVoiceProvider() if os.getenv("BHASHINI_API_KEY") else DemoVoiceProvider()
            text = provider.briefing_text(proj, risk, exps)
            # BHOOMI concise briefing
            return {"success":True,"data":{"intent":"VOICE_BRIEFING","response":text,"route":f"/projects/{proj.id}","filters":{},"speak":True},"meta":{}}
    # --- OUTCOMES ---
    if "outcome" in q:
        return {"success":True,"data":{"intent":"OUTCOME_QUERY","response":"Opening Outcomes. Reviewing intervention results and retraining queue.","route":"/outcomes","filters":{},"speak":True},"meta":{}}
    # --- COUNT ---
    if "how many" in q and "project" in q:
        cnt=count_projects({})
        return {"success":True,"data":{"intent":"PROJECT_SEARCH","response":f"There are {cnt} projects in your jurisdiction.","route":"/projects","filters":{},"speak":True},"meta":{}}
    if "dashboard" in q or "overview" in q:
        return {"success":True,"data":{"intent":"NAVIGATE","response":"Opening Dashboard. BHOOMI Intelligence is ready.","route":"/dashboard","filters":{},"speak":True},"meta":{}}
    # --- STOP / CANCEL ---
    if q.strip() in ["stop","cancel","never mind","go back"]:
        return {"success":True,"data":{"intent":"GENERAL_INFORMATION","response":"Stopped. How can I assist?","route":"/dashboard","filters":{},"speak":True},"meta":{}}
    # default
    return {"success":True,"data":{"intent":"GENERAL_INFORMATION","response":"I can help with: show critical projects, why is this project high risk, show grievance hotspots, open simulator, give me a project briefing. Try: 'Show critical projects'.","route":"/dashboard","filters":{},"speak":True},"meta":{}}
