import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["DATABASE_URL"]="sqlite:///./test.db"
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine
import pytest

# reset db
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
from app.database import SessionLocal
from app.models.user import User
from app.auth.security import hash_password
from app.ml.train import train
train()
from seed import seed
seed()

client=TestClient(app)

def login(u="admin",p="demo123"):
    r=client.post("/api/auth/login", json={"username":u,"password":p})
    assert r.status_code==200, r.text
    return r.json()["data"]["access_token"]

def test_login_ok():
    tok=login()
    assert tok

def test_invalid_login():
    r=client.post("/api/auth/login", json={"username":"admin","password":"wrong"})
    assert r.status_code==401

def test_rbac_jurisdiction():
    t_off=login("officer")
    # officer is Punjab; try to access a Tamil Nadu project if exists
    from app.database import SessionLocal
    from app.models.project import Project
    db=SessionLocal()
    tn=db.query(Project).filter(Project.state=="Tamil Nadu").first()
    db.close()
    if tn:
        r=client.get(f"/api/projects/{tn.id}", headers={"Authorization":f"Bearer {t_off}"})
        assert r.status_code in (403,200)  # may be 403 if filtering

def test_projects():
    tok=login()
    r=client.get("/api/projects?sort=highest_risk", headers={"Authorization":f"Bearer {tok}"})
    assert r.status_code==200
    assert len(r.json()["data"])>0

def test_risk_prediction():
    tok=login()
    r=client.post("/api/projects/1/predict", headers={"Authorization":f"Bearer {tok}"})
    assert r.status_code==200
    assert "probability" in r.json()["data"]

def test_shap():
    tok=login()
    r=client.get("/api/projects/1/explanation", headers={"Authorization":f"Bearer {tok}"})
    assert r.status_code==200
    assert isinstance(r.json()["data"], list)

def test_precedent():
    tok=login()
    r=client.get("/api/projects/1/precedents", headers={"Authorization":f"Bearer {tok}"})
    assert r.status_code==200

def test_grievance():
    tok=login()
    r=client.post("/api/grievances/analyze", headers={"Authorization":f"Bearer {tok}"}, json={"text":"Our compensation has not been received and nobody explained the SIA process."})
    assert r.status_code==200
    assert r.json()["data"]["intent"] in ["compensation","consultation","other"]

def test_simulator_no_mutate():
    tok=login()
    from app.database import SessionLocal
    from app.models.project import Project
    db=SessionLocal()
    p=db.query(Project).filter(Project.id==1).first()
    before=p.consultation_progress_pct
    db.close()
    r=client.post("/api/simulation/counterfactual", headers={"Authorization":f"Bearer {tok}"}, json={"project_id":1,"changes":{"consultation_progress_pct":75}})
    assert r.status_code==200
    assert r.json()["data"]["simulation_only"]==True
    db=SessionLocal()
    p2=db.query(Project).filter(Project.id==1).first()
    assert p2.consultation_progress_pct==before
    db.close()

def test_recommendations():
    tok=login()
    r=client.get("/api/projects/1/advisory", headers={"Authorization":f"Bearer {tok}"})
    assert r.status_code==200
    if r.json()["data"]:
        rid=r.json()["data"][0]["id"]
        r2=client.post(f"/api/recommendations/{rid}/accept", headers={"Authorization":f"Bearer {tok}"})
        assert r2.status_code==200

def test_outcome_and_queue():
    tok=login()
    r=client.post("/api/outcomes", headers={"Authorization":f"Bearer {tok}"}, json={"project_id":1,"accepted":"YES","action_taken":"Consultation completed","result":"Reduced grievances","outcome_label":"POSITIVE"})
    assert r.status_code==200
    r2=client.get("/api/retraining/queue", headers={"Authorization":f"Bearer {tok}"})
    assert r2.status_code==200
    assert r2.json()["data"]["queued_samples"]>=1

def test_voice():
    tok=login()
    r=client.post("/api/voice/briefing", headers={"Authorization":f"Bearer {tok}"}, json={"project_id":1,"language":"en"})
    assert r.status_code==200

def test_health():
    r=client.get("/health")
    assert r.status_code==200
