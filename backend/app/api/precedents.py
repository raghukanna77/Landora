from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.project import Project
from ..models.risk import RiskPrediction
from ..auth.security import get_current_user
from ..models.user import User
from ..gis.spatial import similarity_score, haversine, pattern_for

router = APIRouter()

@router.get("/projects/{pid}/precedents")
def precedents(pid:int, limit:int=5, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    p=db.query(Project).filter(Project.id==pid).first()
    if not p: raise HTTPException(404,"Not found")
    others=db.query(Project).filter(Project.id!=pid).all()
    scored=[]
    for o in others:
        sim=similarity_score(p,o)
        dist=None
        if p.latitude and p.longitude and o.latitude and o.longitude:
            dist=haversine(p.latitude,p.longitude,o.latitude,o.longitude)
        pred=db.query(RiskPrediction).filter(RiskPrediction.project_id==o.id).order_by(RiskPrediction.prediction_timestamp.desc()).first()
        scored.append({"reference_project_id":o.id,"reference_project":o.name,"state":o.state,"district":o.district,"stage":o.current_stage,"similarity":round(sim,3),"distance_km":round(dist,1) if dist else None,"historical_delay": pred.probability>=0.5 if pred else False,"pattern":pattern_for(o),"project_code":o.project_code})
    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return {"success":True,"data":scored[:limit],"meta":{}}
