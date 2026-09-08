from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.project import Project
from ..models.risk import Recommendation, AuditLog
from ..auth.security import get_current_user
from ..models.user import User
from ..ml.explain import explain_project
from ..services.recommendation_service import generate_recommendations

router = APIRouter()

@router.get("/projects/{pid}/advisory")
def advisory(pid:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    p=db.query(Project).filter(Project.id==pid).first()
    if not p: raise HTTPException(404,"Not found")
    exps=explain_project(p)
    # check existing? generate fresh if none pending
    existing=db.query(Recommendation).filter(Recommendation.project_id==pid, Recommendation.status=="PENDING").all()
    if existing:
        data=[{"id":r.id,"project_id":r.project_id,"stage":r.stage,"action":r.action,"owner_role":r.owner_role,"priority":r.priority,"reason":r.reason,"predicted_risk_reduction":r.predicted_risk_reduction,"status":r.status} for r in existing]
        return {"success":True,"data":data,"meta":{}}
    # generate from service
    from ..ml.predict import predict_for_project
    pred=predict_for_project(p)
    recs=generate_recommendations(p, exps, pred["probability"])
    created=[]
    for rec in recs:
        r=Recommendation(project_id=pid, stage=p.current_stage, action=rec["action"], owner_role=rec["owner_role"], priority=rec["priority"], reason=rec["reason"], predicted_risk_reduction=rec["predicted_risk_reduction"])
        db.add(r)
    db.commit()
    # return
    rows=db.query(Recommendation).filter(Recommendation.project_id==pid, Recommendation.status=="PENDING").all()
    return {"success":True,"data":[{"id":r.id,"project_id":r.project_id,"stage":r.stage,"action":r.action,"owner_role":r.owner_role,"priority":r.priority,"reason":r.reason,"predicted_risk_reduction":r.predicted_risk_reduction,"status":r.status} for r in rows],"meta":{}}

@router.post("/recommendations/{rid}/accept")
def accept(rid:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    r=db.query(Recommendation).filter(Recommendation.id==rid).first()
    if not r: raise HTTPException(404,"Not found")
    r.status="ACCEPTED"
    db.add(AuditLog(user_id=user.id, action="recommendation_accept", resource_type="recommendation", resource_id=str(rid)))
    db.commit()
    return {"success":True,"data":{"id":r.id,"status":r.status},"meta":{}}
@router.post("/recommendations/{rid}/reject")
def reject(rid:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    r=db.query(Recommendation).filter(Recommendation.id==rid).first()
    if not r: raise HTTPException(404,"Not found")
    r.status="REJECTED"
    db.add(AuditLog(user_id=user.id, action="recommendation_reject", resource_type="recommendation", resource_id=str(rid)))
    db.commit()
    return {"success":True,"data":{"id":r.id,"status":r.status},"meta":{}}
@router.post("/recommendations/{rid}/defer")
def defer(rid:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    r=db.query(Recommendation).filter(Recommendation.id==rid).first()
    if not r: raise HTTPException(404,"Not found")
    r.status="DEFERRED"
    db.add(AuditLog(user_id=user.id, action="recommendation_defer", resource_type="recommendation", resource_id=str(rid)))
    db.commit()
    return {"success":True,"data":{"id":r.id,"status":r.status},"meta":{}}
