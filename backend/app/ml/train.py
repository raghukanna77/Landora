import os, json, joblib, numpy as np, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, average_precision_score, precision_score, recall_score, f1_score, confusion_matrix, brier_score_loss
from sklearn.calibration import CalibratedClassifierCV
import lightgbm as lgb
from .features import FEATURE_COLS, CATEGORICAL, NUMERIC

ARTIFACT_DIR = os.environ.get("MODEL_PATH", "./ml/artifacts/model.joblib")
if ARTIFACT_DIR.endswith("model.joblib"):
    ARTIFACT_DIR = os.path.dirname(ARTIFACT_DIR)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def generate_synthetic(n=1000, seed=42):
    rng = np.random.RandomState(seed)
    states = ["Punjab","Tamil Nadu","Gujarat","Bihar","Karnataka","Maharashtra","Rajasthan","Uttar Pradesh","Madhya Pradesh","West Bengal"]
    districts_map = {
        "Punjab":["Amritsar","Ludhiana","Patiala","Jalandhar"],
        "Tamil Nadu":["Chennai","Coimbatore","Madurai","Salem"],
        "Gujarat":["Ahmedabad","Surat","Vadodara","Rajkot"],
        "Bihar":["Patna","Gaya","Muzaffarpur","Bhagalpur"],
        "Karnataka":["Bengaluru","Mysuru","Hubli","Mangaluru"],
        "Maharashtra":["Mumbai","Pune","Nagpur","Nashik"],
        "Rajasthan":["Jaipur","Jodhpur","Udaipur","Kota"],
        "Uttar Pradesh":["Lucknow","Kanpur","Varanasi","Agra"],
        "Madhya Pradesh":["Bhopal","Indore","Jabalpur","Gwalior"],
        "West Bengal":["Kolkata","Howrah","Durgapur","Siliguri"],
    }
    stages = ["Notification","SIA","Consent","Award","Compensation","Possession"]
    sizes = ["SMALL","MEDIUM","LARGE","MEGA"]
    rows=[]
    for i in range(n):
        state = rng.choice(states)
        district = rng.choice(districts_map[state])
        stage = rng.choice(stages)
        size = rng.choice(sizes, p=[0.25,0.35,0.25,0.15])
        affected_landowners = int(rng.gamma(4,20)+10)
        affected_area = float(rng.gamma(5,10)+5)
        grievances = int(max(0, rng.poisson(12) + (affected_landowners/30) * rng.rand()))
        growth = float(rng.uniform(-0.1, 0.6))
        compensation_pending_pct = float(np.clip(rng.normal(35,20),0,100))
        notification_age_days = int(rng.randint(10, 400))
        document_completeness_pct = float(np.clip(rng.normal(78,15),30,100))
        legal_disputes = int(rng.poisson(2))
        consultation_progress_pct = float(np.clip(rng.normal(60,20),10,100))
        utility_conflicts = int(rng.poisson(2))
        land_records_match_pct = float(np.clip(rng.normal(82,12),40,100))
        pending_clearances = int(rng.poisson(2))
        historical_regional_delay_rate = float(rng.uniform(0.15,0.55))
        historical_stage_delay_rate = {"Notification":0.25,"SIA":0.45,"Consent":0.4,"Award":0.3,"Compensation":0.5,"Possession":0.35}[stage] + rng.normal(0,0.05)
        # latent risk — amplified for demo discriminability
        score = (
            0.28*(grievances/35)
            +0.22*(compensation_pending_pct/100)
            +0.20*(1-consultation_progress_pct/100)
            +0.14*(legal_disputes/7)
            +0.10*(1-document_completeness_pct/100)
            +0.09*(1-land_records_match_pct/100)
            +0.06*(utility_conflicts/5)
            +0.05*(pending_clearances/5)
            +0.04*(notification_age_days/350)
            +0.04*(historical_regional_delay_rate)
            +0.04*(historical_stage_delay_rate)
        )
        if size=="MEGA": score+=0.08
        if size=="LARGE": score+=0.04
        prob = 1/(1+np.exp(-(score*10-4.0)))
        prob = np.clip(prob + rng.normal(0,0.03),0.05,0.95)
        delay = int(rng.binomial(1, prob))
        rows.append({
            "state":state,"district":district,"stage":stage,"project_size":size,
            "affected_landowners":affected_landowners,"affected_area":affected_area,
            "grievances":grievances,"grievance_growth_rate":growth,
            "compensation_pending_pct":compensation_pending_pct,"notification_age_days":notification_age_days,
            "document_completeness_pct":document_completeness_pct,"legal_disputes":legal_disputes,
            "consultation_progress_pct":consultation_progress_pct,"utility_conflicts":utility_conflicts,
            "land_records_match_pct":land_records_match_pct,"pending_clearances":pending_clearances,
            "historical_regional_delay_rate":historical_regional_delay_rate,"historical_stage_delay_rate":historical_stage_delay_rate,
            "delay":delay,"prob":prob
        })
    return pd.DataFrame(rows)

def train(df=None, model_version="lightgbm-v1"):
    if df is None:
        df = generate_synthetic(1000, seed=42)
    X = df[FEATURE_COLS + CATEGORICAL]
    y = df["delay"]
    # temporal-like split random but stratified
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    X_train2, X_val, y_train2, y_val = train_test_split(X_train, y_train, test_size=0.15, random_state=43, stratify=y_train)
    # preprocessor: encode categoricals, pass numeric
    # Use OneHotEncoder for categoricals
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
        ("num", "passthrough", NUMERIC),
    ])
    base = lgb.LGBMClassifier(n_estimators=200, learning_rate=0.05, max_depth=6, random_state=42, verbose=-1)
    pipe = Pipeline([("pre", pre), ("model", base)])
    pipe.fit(X_train2, y_train2)
    # calibration on val - try CalibratedClassifierCV, fallback to pipe directly
    try:
        cal = CalibratedClassifierCV(pipe, method="sigmoid", cv="prefit")
        cal.fit(X_val, y_val)
    except Exception as e:
        # fallback: no calibration, use pipe directly
        cal = pipe
    # Evaluate
    prob = cal.predict_proba(X_test)[:,1]
    pred = (prob>=0.5).astype(int)
    metrics = {
        "roc_auc": float(roc_auc_score(y_test, prob)),
        "pr_auc": float(average_precision_score(y_test, prob)),
        "precision": float(precision_score(y_test, pred, zero_division=0)),
        "recall": float(recall_score(y_test, pred, zero_division=0)),
        "f1": float(f1_score(y_test, pred, zero_division=0)),
        "brier": float(brier_score_loss(y_test, prob)),
        "confusion": confusion_matrix(y_test, pred).tolist(),
    }
    # per stage
    df_test = X_test.copy()
    df_test["y_true"]=y_test.values
    df_test["prob"]=prob
    df_test["pred"]=pred
    by_stage={}
    for s in df_test["stage"].unique():
        sub=df_test[df_test["stage"]==s]
        if len(sub)>5:
            try:
                by_stage[s]=float(roc_auc_score(sub["y_true"], sub["prob"]))
            except: by_stage[s]=None
    metrics["by_stage_auc"]=by_stage
    # save
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    joblib.dump(cal, os.path.join(ARTIFACT_DIR, "model.joblib"))
    # also dump feature order
    with open(os.path.join(ARTIFACT_DIR, "metrics.json"),"w") as f:
        json.dump(metrics,f,indent=2)
    with open(os.path.join(ARTIFACT_DIR, "model_version.json"),"w") as f:
        json.dump({"model_version":model_version},f)
    return cal, metrics

if __name__ == "__main__":
    _, m = train()
    print(m)
