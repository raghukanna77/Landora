from datetime import datetime, timedelta
from jose import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..config import settings
from ..database import get_db
from ..models.user import User
import hashlib

security = HTTPBearer()

def hash_password(p: str) -> str:
    # Use sha256 for demo portability (avoid passlib/bcrypt version issues)
    return hashlib.sha256(p.encode()).hexdigest()

def verify_password(p, h) -> bool:
    return hashlib.sha256(p.encode()).hexdigest() == h

def create_token(data: dict, expires_delta=None):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta or settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

def require_roles(*roles):
    def checker(user: User = Depends(get_current_user)):
        if user.role not in roles and user.role != "ADMIN":
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return checker

def can_access_project(user: User, project) -> bool:
    if user.role in ("ADMIN", "NATIONAL_REVIEWER"):
        return True
    if user.role in ("STATE_OFFICER", "LAND_ACQUISITION_OFFICER", "REVENUE_OFFICER", "LEGAL_OFFICER", "PROJECT_MANAGER", "DISTRICT_OFFICER"):
        if user.state and user.state != project.state:
            return False
        if user.role == "DISTRICT_OFFICER" and user.district and user.district != project.district:
            return False
        return True
    if user.role == "CITIZEN_VIEW":
        return True
    return False
