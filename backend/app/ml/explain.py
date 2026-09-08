import pandas as pd
import numpy as np
from .features import human_explanation_for, direction_for, FEATURE_COLS, CATEGORICAL
from .predict import load_model

def explain_project(project, top_k=5):
    model = load_model()
    # Extract calibrated pipeline: CalibratedClassifierCV wraps pipeline
    # Get base estimator pipeline
    try:
        base_pipe = model.base_estimator
    except AttributeError:
        try:
            base_pipe = model.calibrated_classifiers_[0].estimator
        except:
            base_pipe = model
    # Try to get underlying model and preprocessor
    # We'll attempt SHAP TreeExplainer on the LGBM model inside pipeline
    explanations=[]
    try:
        import shap
        # need transformed features? For SHAP we need to explain with transformed matrix
        # Get preprocessor and model
        # pipe is Pipeline([pre, model])
        # base_pipe should be Pipeline
        if hasattr(base_pipe, "named_steps"):
            pre = base_pipe.named_steps["pre"]
            lgb_model = base_pipe.named_steps["model"]
            # Build feature row
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
            X_tr = pre.transform(df)
            # get feature names after encoding
            cat_enc = pre.named_transformers_["cat"]
            cat_names = list(cat_enc.get_feature_names_out(CATEGORICAL))
            all_names = cat_names + FEATURE_COLS
            explainer = shap.TreeExplainer(lgb_model)
            shap_values = explainer.shap_values(X_tr)
            if isinstance(shap_values, list):
                shap_values = shap_values[1] if len(shap_values)>1 else shap_values[0]
            shap_values = np.array(shap_values).flatten()
            # map to names
            contribs = list(zip(all_names, shap_values))
            # sort by abs value
            contribs_sorted = sorted(contribs, key=lambda x: abs(x[1]), reverse=True)[:top_k]
            # But we want human friendly aggregation: map one-hot back to original feature if needed
            # Simplify: for one-hot features, collapse to original categorical name and sum
            # For now return top contribs with collapsed logic
            # We'll aggregate one-hot SHAP for each categorical group for ranking but keep detailed leaf for explanation?
            # Let's produce collapsed ranking: sum abs per original feature group
            # First build dict of aggregated contributions for categorical groups
            agg = {}
            for name, val in contribs:
                # check if name is one-hot: contains "_"
                base = None
                for cat in CATEGORICAL:
                    if name.startswith(cat+"_"):
                        base = cat
                        break
                key = base if base else name
                agg[key] = agg.get(key, 0) + val
            # sort aggregated
            agg_sorted = sorted(agg.items(), key=lambda x: abs(x[1]), reverse=True)[:top_k]
            explanations=[]
            for feat, contrib in agg_sorted:
                explanations.append({
                    "feature": feat,
                    "contribution": float(contrib),
                    "direction": direction_for(contrib),
                    "human_explanation": human_explanation_for(feat, contrib)
                })
            return explanations
    except Exception as e:
        # fallback: use simple heuristic importance
        pass
    # Fallback heuristic based on feature values
    # Compute simple normalized risk drivers
    drivers = [
        ("grievances", (project.grievances/40)*0.31),
        ("consultation_progress_pct", (1-project.consultation_progress_pct/100)*0.27),
        ("legal_disputes", (project.legal_disputes/8)*0.19),
        ("document_completeness_pct", (1-project.document_completeness_pct/100)*0.14),
        ("land_records_match_pct", (1-project.land_records_match_pct/100)*0.08),
        ("compensation_pending_pct", (project.compensation_pending_pct/100)*0.15),
    ]
    # assign direction: if value indicates risk, positive else negative
    # For calibration we just show positive contributions for high-risk features
    result=[]
    for feat, contrib in sorted(drivers, key=lambda x: x[1], reverse=True)[:top_k]:
        # adjust sign: if feat is progress/match/completeness, low value => positive contribution, else high => positive
        # Drivers already computed as positive where risk
        result.append({
            "feature": feat,
            "contribution": float(contrib),
            "direction": "increases risk",
            "human_explanation": human_explanation_for(feat, contrib)
        })
    return result
