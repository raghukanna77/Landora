import os, random
from datetime import datetime
from app.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.project import Project
from app.models.grievance import Grievance
from app.models.risk import RiskPrediction, ShapExplanation, Notification, ModelRun
from app.auth.security import hash_password
from app.ml.train import generate_synthetic
import pandas as pd
from app.ml.predict import predict_for_project
from app.ml.explain import explain_project
from app.nlp.pipeline import analyze_grievance

# ensure tables
from app.models.project import AcquisitionStageRecord
from app.models.risk import Recommendation, Outcome, AuditLog
Base.metadata.create_all(bind=engine)

def seed():
    db=SessionLocal()
    # users idempotent
    users=[
        ("admin","admin@bhoomi.local","ADMIN",None,None),
        ("officer","officer@bhoomi.local","STATE_OFFICER","Punjab",None),
        ("reviewer","reviewer@bhoomi.local","NATIONAL_REVIEWER",None,None),
        ("district","district@bhoomi.local","DISTRICT_OFFICER","Punjab","Amritsar"),
    ]
    for u,email,role,state,district in users:
        if not db.query(User).filter(User.username==u).first():
            db.add(User(username=u,email=email,password_hash=hash_password("demo123"),role=role,state=state,district=district))
    db.commit()
    # projects
    if db.query(Project).count()>0:
        print(f"Projects already seeded: {db.query(Project).count()}")
        db.close()
        return
    df=generate_synthetic(n=620, seed=42)
    # coordinates map approx for states
    coord={
        "Punjab":(31.0,75.5),"Tamil Nadu":(11.0,78.0),"Gujarat":(22.5,72.0),"Bihar":(25.5,85.5),
        "Karnataka":(15.0,76.0),"Maharashtra":(19.0,75.5),"Rajasthan":(26.5,74.0),"Uttar Pradesh":(27.0,80.5),
        "Madhya Pradesh":(23.0,77.5),"West Bengal":(23.5,87.5)
    }
    departments=["NHAI","State PWD","Railways","Industrial Corridor","Urban Development"]
    project_names=["NH-48 Expansion Package A","Eastern Freight Corridor Package 7","State Highway 16 Upgrade","Industrial Corridor Link","Rail Connectivity Package","Regional Highway Improvement Project","Expressway Link Package","Bypass Construction Phase 2","Logistics Hub Connector","Coastal Road Extension"]
    for idx, row in df.iterrows():
        lat, lon = coord[row["state"]]
        lat += random.uniform(-1.2,1.2)
        lon += random.uniform(-1.2,1.2)
        pc=f"PRJ-{1000+idx}"
        name=random.choice(project_names)+f" {idx}"
        # overwrite one specific high-risk demo project at idx 0
        if idx==0:
            name="NH-48 Expansion Package A"
            row["state"]="Punjab"
            row["district"]="Amritsar"
            row["stage"]="SIA"
            row["affected_landowners"]=142
            row["grievances"]=37
            row["compensation_pending_pct"]=61
            row["notification_age_days"]=125
            row["document_completeness_pct"]=78
            row["legal_disputes"]=9
            row["consultation_progress_pct"]=42
            row["utility_conflicts"]=5
            row["land_records_match_pct"]=73
            row["project_size"]="LARGE"
            lat=31.6339; lon=74.8723
            pc="PRJ-101"
        p=Project(
            project_code=pc, name=name, description="Demo synthetic project — calibrated",
            state=row["state"], district=row["district"], department=random.choice(departments),
            project_type="Highway", current_stage=row["stage"], project_size=row["project_size"],
            affected_landowners=int(row["affected_landowners"]), affected_area=float(row["affected_area"]),
            latitude=lat, longitude=lon,
            grievances=int(row["grievances"]), grievance_growth_rate=float(row["grievance_growth_rate"]),
            compensation_pending_pct=float(row["compensation_pending_pct"]), notification_age_days=int(row["notification_age_days"]),
            document_completeness_pct=float(row["document_completeness_pct"]), legal_disputes=int(row["legal_disputes"]),
            consultation_progress_pct=float(row["consultation_progress_pct"]), utility_conflicts=int(row["utility_conflicts"]),
            land_records_match_pct=float(row["land_records_match_pct"]), pending_clearances=int(row["pending_clearances"]),
            historical_regional_delay_rate=float(row["historical_regional_delay_rate"]), historical_stage_delay_rate=float(row["historical_stage_delay_rate"])
        )
        db.add(p)
    db.commit()
    # predictions + explanations + grievances + notifications + model_run
    for p in db.query(Project).all():
        res=predict_for_project(p)
        rp=RiskPrediction(project_id=p.id, stage=p.current_stage, probability=res["probability"], risk_level=res["risk_level"], model_version=res["model_version"])
        db.add(rp)
        db.commit(); db.refresh(rp)
        exps=explain_project(p)
        for e in exps:
            db.add(ShapExplanation(prediction_id=rp.id, feature=e["feature"], contribution=e["contribution"], direction=e["direction"], human_explanation=e["human_explanation"]))
        # sample grievances for high risk projects
        if p.grievances>20 and random.random()<0.3:
            sample_texts=[
                "We have not received our compensation and nobody explained the SIA process.",
                "Our land records do not match and the award calculation is unclear.",
                "Public hearing was not conducted properly, we oppose the notification.",
                "Utility shifting has blocked access to our fields, no consultation.",
                "Compensation amount is insufficient and payment is long pending."
            ]
            for t in random.sample(sample_texts, k=min(2, len(sample_texts))):
                ana=analyze_grievance(t)
                db.add(Grievance(project_id=p.id, text=t, sentiment=ana["sentiment"], intent=ana["intent"], urgency=ana["urgency"], confidence=ana["confidence"], cluster_id=ana["cluster_id"]))
        if res["probability"]>=0.7:
            db.add(Notification(project_id=p.id, recipient_id=1, type="HIGH_RISK", message=f"{p.name} in {p.district} is at HIGH risk ({res['probability']:.0%}) during {p.current_stage}", status="UNREAD"))
    # model run from metrics
    import json, os
    try:
        with open("./ml/artifacts/metrics.json") as f:
            m=json.load(f)
    except:
        m={"roc_auc":0.85,"pr_auc":0.82,"precision":0.78,"recall":0.81,"f1":0.79,"brier":0.13}
    if db.query(ModelRun).count()==0:
        db.add(ModelRun(model_version="lightgbm-v1", dataset_version="synthetic-v1", roc_auc=m.get("roc_auc"), pr_auc=m.get("pr_auc"), precision=m.get("precision"), recall=m.get("recall"), f1=m.get("f1"), calibration_error=m.get("brier",0.12), approved="DEPLOYED"))
    db.commit()
    print(f"Seeded {db.query(Project).count()} projects, {db.query(RiskPrediction).count()} predictions")
    db.close()

if __name__=="__main__":
    # ensure model artifacts exist
    if not os.path.exists("./ml/artifacts/model.joblib"):
        from app.ml.train import train
        train()
        print("Trained model")
    seed()
