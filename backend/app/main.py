from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
from .config import settings
from .database import Base, engine, init_db, SessionLocal
from .api import auth as auth_api, dashboard as dash_api, projects as proj_api, risk as risk_api, grievances as griev_api, precedents as prec_api, simulator as sim_api, recommendations as rec_api, outcomes as out_api, model as model_api, notifications as notif_api, voice as voice_api, ingestion as ingest_api, complaints as complaint_api

# Models for table creation
from .models.user import User
from .models.project import Project, AcquisitionStageRecord
from .models.grievance import Grievance
from .models.complaint import Complaint
from .models.risk import RiskPrediction, ShapExplanation, PrecedentMatch, Recommendation, Outcome, ModelRun, Notification, AuditLog

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init DB + seed if empty (for Render's ephemeral FS, first boot)
    init_db()
    try:
        db = SessionLocal()
        from sqlalchemy import text as sql_text
        # Check if users table empty, then seed
        cnt = db.query(User).count()
        if cnt == 0:
            print("No users found, seeding demo data...")
            # Ensure artifacts exist (don't fail if libgomp missing — we have fallback heuristic)
            import os as _os
            if not _os.path.exists("./ml/artifacts/model.joblib"):
                try:
                    from .ml.train import train as train_model
                    train_model()
                    print("Model trained")
                except Exception as e:
                    print(f"Model train failed (fallback will be used): {e}")
            # Seed
            try:
                from seed import seed as run_seed
                run_seed()
                print("Seed complete")
            except Exception as e:
                print(f"Seed failed: {e}")
                # Fallback: try import from backend/seed.py
                import importlib.util, pathlib
                spec = importlib.util.spec_from_file_location("seed_mod", "seed.py")
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)  # type: ignore
                    mod.seed()
        db.close()
    except Exception as e:
        print(f"Startup seed check failed: {e}")
    yield

app = FastAPI(title="Bhoomi-Drishti API", version="1.0.0", description="AI-Powered Predictive Land Acquisition Delay Intelligence — Decision Support Layer", lifespan=lifespan)

origins = settings.get_cors_origins()
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
@app.get("/")
def root():
    return {"success": True, "data": {"service":"Bhoomi-Drishti API", "docs":"/docs", "health":"/health", "frontend": settings.FRONTEND_URL or "not configured"}, "meta":{}}

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

# Optionally serve frontend static if built and placed in backend/static (for single-service deploy)
if os.path.exists("static"):
    app.mount("/app", StaticFiles(directory="static", html=True), name="static")
