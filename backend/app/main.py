from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import Base, engine
from .api import auth as auth_api, dashboard as dash_api, projects as proj_api, risk as risk_api, grievances as griev_api, precedents as prec_api, simulator as sim_api, recommendations as rec_api, outcomes as out_api, model as model_api, notifications as notif_api, voice as voice_api, ingestion as ingest_api, complaints as complaint_api

# Create tables
from .models.user import User
from .models.project import Project, AcquisitionStageRecord
from .models.grievance import Grievance
from .models.complaint import Complaint
from .models.risk import RiskPrediction, ShapExplanation, PrecedentMatch, Recommendation, Outcome, ModelRun, Notification, AuditLog

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bhoomi-Drishti API", version="1.0.0", description="AI-Powered Predictive Land Acquisition Delay Intelligence — Decision Support Layer")

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"success": True, "data": {"status":"ONLINE", "service":"Bhoomi-Drishti"}, "meta":{}}
@app.get("/ready")
def ready():
    return {"success": True, "data": {"ready": True}, "meta":{}}
@app.get("/metrics")
def metrics():
    return {"success": True, "data": {"uptime":"demo"}, "meta":{}}

app.include_router(auth_api.router, prefix="/api/auth", tags=["auth"])
app.include_router(dash_api.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(proj_api.router, prefix="/api/projects", tags=["projects"])
app.include_router(risk_api.router, prefix="/api", tags=["risk"])
app.include_router(griev_api.router, prefix="/api", tags=["grievances"])
app.include_router(prec_api.router, prefix="/api", tags=["precedents"])
app.include_router(sim_api.router, prefix="/api/simulation", tags=["simulation"])
app.include_router(rec_api.router, prefix="/api", tags=["recommendations"])
app.include_router(out_api.router, prefix="/api", tags=["outcomes"])
app.include_router(model_api.router, prefix="/api", tags=["model"])
app.include_router(notif_api.router, prefix="/api", tags=["notifications"])
app.include_router(voice_api.router, prefix="/api/voice", tags=["voice"])
app.include_router(ingest_api.router, prefix="/api/ingestion", tags=["ingestion"])
app.include_router(complaint_api.router, prefix="/api", tags=["complaints"])
