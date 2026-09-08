from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..auth.security import hash_password, verify_password, create_token, get_current_user
from pydantic import BaseModel
from datetime import datetime
from ..models.risk import AuditLog

router = APIRouter()

class LoginReq(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(req: LoginReq, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username==req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({"sub": user.username, "role": user.role})
    db.add(AuditLog(user_id=user.id, action="login", resource_type="auth", resource_id=user.username))
    db.commit()
    return {"success": True, "data": {"access_token": token, "token_type":"bearer", "user":{"id":user.id,"username":user.username,"role":user.role,"state":user.state,"district":user.district}}, "meta":{}}
@router.post("/refresh")
def refresh(user: User = Depends(get_current_user)):
    token = create_token({"sub": user.username, "role": user.role})
    return {"success": True, "data": {"access_token": token}, "meta":{}}
@router.post("/logout")
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.add(AuditLog(user_id=user.id, action="logout", resource_type="auth", resource_id=user.username))
    db.commit()
    return {"success": True, "data": {"message":"Logged out"}, "meta":{}}
@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"success": True, "data": {"id":user.id,"username":user.username,"role":user.role,"state":user.state,"district":user.district,"email":user.email}, "meta":{}}
