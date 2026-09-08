from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import get_db
from ..models.risk import Notification
from ..auth.security import get_current_user
from ..models.user import User

router=APIRouter()

@router.get("/notifications")
def list_notifs(db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    rows=db.query(Notification).order_by(Notification.created_at.desc()).limit(50).all()
    return {"success":True,"data":[{"id":r.id,"project_id":r.project_id,"type":r.type,"message":r.message,"status":r.status,"created_at":r.created_at.isoformat()} for r in rows],"meta":{}}
@router.post("/notifications/test")
def test(payload: dict=None, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    n=Notification(project_id=payload.get("project_id") if payload else None, recipient_id=user.id, type="TEST", message="Test notification — DEMO MODE")
    db.add(n); db.commit()
    return {"success":True,"data":{"id":n.id},"meta":{}}
