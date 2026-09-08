from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import re
from ..database import get_db
from ..models.complaint import Complaint, generate_complaint_id
from ..models.project import Project
from ..models.grievance import Grievance
from ..models.risk import RiskPrediction, ShapExplanation, Notification, AuditLog
from ..nlp.pipeline import analyze_grievance
from ..auth.security import get_current_user
from ..models.user import User

router = APIRouter()

STATE_CODE_MAP = {
    "Punjab":"PB","Tamil Nadu":"TN","Gujarat":"GJ","Bihar":"BR","Karnataka":"KA","Maharashtra":"MH","Rajasthan":"RJ","Uttar Pradesh":"UP","Madhya Pradesh":"MP","West Bengal":"WB"
}

CATEGORY_STAGE = {
    "Compensation":"Compensation",
    "Land Record":"Award",
    "Ownership":"Consent",
    "Survey":"SIA",
    "Legal Issue":"Award",
    "Rehabilitation & Resettlement":"Possession",
    "Possession":"Possession",
    "Notification":"Notification",
    "Other":"SIA"
}

class PublicComplaintCreate(BaseModel):
    project_name: str
    state: str
    district: str
    village: Optional[str]=None
    project_id: Optional[int]=None
    category: str
    details: str
    latitude: Optional[float]=None
    longitude: Optional[float]=None
    contact_preference: str = "anonymous"  # with_contact / anonymous
    name: Optional[str]=None
    mobile: Optional[str]=None
    email: Optional[str]=None

@router.post("/complaints/public")
def submit_public(payload: PublicComplaintCreate, db: Session = Depends(get_db)):
    # validate
    if not payload.project_name or not payload.details:
        raise HTTPException(400, "Project name and details required")
    if payload.latitude and not (-90 <= payload.latitude <= 90):
        raise HTTPException(400, "Invalid latitude")
    if payload.longitude and not (-180 <= payload.longitude <= 180):
        raise HTTPException(400, "Invalid longitude")
    if payload.contact_preference == "with_contact" and not payload.mobile and not payload.email:
        raise HTTPException(400, "Provide mobile or email for contact")
    # NLP
    ana = analyze_grievance(payload.details)
    stage_mapped = CATEGORY_STAGE.get(payload.category, "SIA")
    # complaint ID
    code = STATE_CODE_MAP.get(payload.state, "XX")
    cid = generate_complaint_id(code)
    # ensure unique
    while db.query(Complaint).filter(Complaint.complaint_id==cid).first():
        cid = generate_complaint_id(code)
    # try to map project_id via name search if not provided
    pid = payload.project_id
    if not pid and payload.project_name:
        # fuzzy: find project by name contains
        cand = db.query(Project).filter(Project.name.ilike(f"%{payload.project_name[:15]}%")).first()
        if cand:
            pid = cand.id
        else:
            # also try state/district exact project
            cand2 = db.query(Project).filter(Project.state==payload.state, Project.district==payload.district).first()
            if cand2:
                pid = cand2.id
    c = Complaint(
        complaint_id=cid,
        project_name=payload.project_name,
        project_id=pid,
        state=payload.state,
        district=payload.district,
        village=payload.village,
        category=payload.category,
        details=payload.details,
        latitude=payload.latitude,
        longitude=payload.longitude,
        contact_preference=payload.contact_preference,
        name=payload.name,
        mobile=payload.mobile,
        email=payload.email,
        intent=ana["intent"],
        sentiment=ana["sentiment"],
        urgency=ana["urgency"],
        confidence=ana["confidence"],
        stage_mapped=stage_mapped,
        status="AI Classified",
        assigned_department="Revenue" if ana["intent"]=="compensation" else "Land Acquisition",
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    # Feed into grievance intelligence if project mapped
    if pid:
        proj = db.query(Project).filter(Project.id==pid).first()
        if proj:
            g = Grievance(project_id=pid, text=payload.details, sentiment=ana["sentiment"], intent=ana["intent"], urgency=ana["urgency"], confidence=ana["confidence"], cluster_id=ana["cluster_id"])
            db.add(g)
            proj.grievances = (proj.grievances or 0) + 1
            # stage mapping: increase urgency signal? For simplicity bump compensation_pending if compensation
            if ana["intent"]=="compensation":
                proj.compensation_pending_pct = min(100, proj.compensation_pending_pct + 2)
            if ana["urgency"]=="HIGH":
                proj.pending_clearances = (proj.pending_clearances or 0) + 1
            db.commit()
            # recalc risk
            from ..ml.predict import predict_for_project
            from ..ml.explain import explain_project
            res = predict_for_project(proj)
            pred = RiskPrediction(project_id=proj.id, stage=proj.current_stage, probability=res["probability"], risk_level=res["risk_level"], model_version=res["model_version"])
            db.add(pred)
            db.commit()
            db.refresh(pred)
            exps = explain_project(proj)
            for e in exps:
                db.add(ShapExplanation(prediction_id=pred.id, feature=e["feature"], contribution=e["contribution"], direction=e["direction"], human_explanation=e["human_explanation"]))
            # notification
            db.add(Notification(project_id=pid, recipient_id=None, type="GRIEVANCE_SPIKE", message=f"New {ana['urgency']} urgency {ana['intent']} complaint {cid} mapped to {proj.name} — risk now {res['probability']:.0%}", status="UNREAD"))
            db.commit()
            # update complaint status to Officer Review
            c.status = "Officer Review"
            db.commit()
    else:
        # still notify unmapped
        db.add(Notification(project_id=None, recipient_id=None, type="UNMAPPED_COMPLAINT", message=f"Unmapped complaint {cid}: {payload.category} in {payload.district}, {payload.state}", status="UNREAD"))
        db.commit()
    return {"success": True, "data": {"complaint_id": cid, "status": c.status, "analysis": ana, "project_mapped": pid, "stage_mapped": stage_mapped}, "meta": {"message": "Complaint submitted. Your complaint helps identify emerging issues — it will be analyzed to prioritize administrative attention."}}

@router.get("/complaints/track/{complaint_id}")
def track(complaint_id: str, db: Session = Depends(get_db)):
    c = db.query(Complaint).filter(Complaint.complaint_id==complaint_id).first()
    if not c:
        raise HTTPException(404, "Complaint ID not found")
    # timeline based on status
    order = ["Submitted","AI Classified","Officer Review","Action Assigned","In Progress","Resolved"]
    idx = order.index(c.status) if c.status in order else 1
    timeline = []
    for i, s in enumerate(order):
        state = "completed" if i < idx else "current" if i==idx else "pending"
        # mark first two as completed always after submission
        if s in ["Submitted","AI Classified"]:
            state = "completed"
        timeline.append({"stage": s, "state": state})
    return {"success": True, "data": {
        "complaint_id": c.complaint_id,
        "project_name": c.project_name,
        "category": c.category,
        "status": c.status,
        "assigned_department": c.assigned_department,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        "analysis": {"intent": c.intent, "sentiment": c.sentiment, "urgency": c.urgency, "stage_mapped": c.stage_mapped},
        "timeline": timeline,
        "resolution_notes": c.resolution_notes,
        "message": "Never expose internal officer details — showing department and stage only"
    }, "meta": {}}

@router.get("/complaints")
def list_complaints(state: Optional[str]=None, district: Optional[str]=None, status: Optional[str]=None, category: Optional[str]=None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(Complaint)
    if user.role not in ("ADMIN","NATIONAL_REVIEWER") and user.state:
        q = q.filter(Complaint.state==user.state)
    if state: q = q.filter(Complaint.state==state)
    if district: q = q.filter(Complaint.district==district)
    if status: q = q.filter(Complaint.status==status)
    if category: q = q.filter(Complaint.category==category)
    rows = q.order_by(Complaint.created_at.desc()).limit(100).all()
    return {"success": True, "data": [{"complaint_id": r.complaint_id, "project_name": r.project_name, "project_id": r.project_id, "state": r.state, "district": r.district, "village": r.village, "category": r.category, "intent": r.intent, "urgency": r.urgency, "status": r.status, "created_at": r.created_at.isoformat() if r.created_at else None, "latitude": r.latitude, "longitude": r.longitude} for r in rows], "meta": {"count": len(rows)}}

@router.get("/complaints/{cid}")
def get_one(cid: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = db.query(Complaint).filter(Complaint.complaint_id==cid).first()
    if not c: raise HTTPException(404, "Not found")
    return {"success": True, "data": {"complaint_id": c.complaint_id, "project_name": c.project_name, "project_id": c.project_id, "state": c.state, "district": c.district, "village": c.village, "category": c.category, "details": c.details, "latitude": c.latitude, "longitude": c.longitude, "status": c.status, "intent": c.intent, "sentiment": c.sentiment, "urgency": c.urgency, "stage_mapped": c.stage_mapped, "created_at": c.created_at.isoformat() if c.created_at else None}, "meta": {}}

@router.post("/complaints/{cid}/status")
def update_status(cid: str, payload: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = db.query(Complaint).filter(Complaint.complaint_id==cid).first()
    if not c: raise HTTPException(404, "Not found")
    new_status = payload.get("status")
    notes = payload.get("resolution_notes")
    if new_status:
        c.status = new_status
    if notes:
        c.resolution_notes = notes
    db.add(AuditLog(user_id=user.id, action="complaint_status_update", resource_type="complaint", resource_id=cid, meta=new_status))
    db.commit()
    return {"success": True, "data": {"complaint_id": cid, "status": c.status}, "meta": {}}
