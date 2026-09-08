import os, joblib, pandas as pd
from ..config import settings, risk_level
from .features import FEATURE_COLS, CATEGORICAL

_model = None

def load_model():
    global _model
    if _model is not None:
        return _model
    path = settings.MODEL_PATH
    # fallback paths
    candidates = [path, "./ml/artifacts/model.joblib", "ml/artifacts/model.joblib", os.path.join(os.path.dirname(__file__), "../../../ml/artifacts/model.joblib")]
    for p in candidates:
        if os.path.exists(p):
            _model = joblib.load(p)
            return _model
    # try train on fly synthetic if not found
    from .train import train
    m,_ = train()
    _model = m
    return _model

def predict_for_project(project) -> dict:
    model = load_model()
    row = {
        "affected_landowners": project.affected_landowners,
        "affected_area": project.affected_area,
        "grievances": project.grievances,
        "grievance_growth_rate": project.grievance_growth_rate,
        "compensation_pending_pct": project.compensation_pending_pct,
        "notification_age_days": project.notification_age_days,
        "document_completeness_pct": project.document_completeness_pct,
        "legal_disputes": project.legal_disputes,
        "consultation_progress_pct": project.consultation_progress_pct,
        "utility_conflicts": project.utility_conflicts,
        "land_records_match_pct": project.land_records_match_pct,
        "pending_clearances": project.pending_clearances,
        "historical_regional_delay_rate": project.historical_regional_delay_rate,
        "historical_stage_delay_rate": project.historical_stage_delay_rate,
        "stage": project.current_stage,
        "state": project.state,
        "district": project.district,
        "project_size": project.project_size,
    }
    df = pd.DataFrame([row])
    prob = float(model.predict_proba(df)[0,1])
    level = risk_level(prob)
    # model version
    import json
    mv="lightgbm-v1"
    try:
        with open("./ml/artifacts/model_version.json") as f:
            mv=json.load(f).get("model_version","lightgbm-v1")
    except: pass
    return {"probability":prob, "risk_level":level, "model_version":mv, "features": row}

def predict_from_dict(feat: dict):
    model = load_model()
    df = pd.DataFrame([feat])
    prob = float(model.predict_proba(df)[0,1])
    return prob, risk_level(prob)
