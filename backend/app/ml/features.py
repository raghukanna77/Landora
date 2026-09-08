FEATURE_COLS = [
    "affected_landowners",
    "affected_area",
    "grievances",
    "grievance_growth_rate",
    "compensation_pending_pct",
    "notification_age_days",
    "document_completeness_pct",
    "legal_disputes",
    "consultation_progress_pct",
    "utility_conflicts",
    "land_records_match_pct",
    "pending_clearances",
    "historical_regional_delay_rate",
    "historical_stage_delay_rate",
]
CATEGORICAL = ["stage", "state", "district", "project_size"]
NUMERIC = FEATURE_COLS

HUMAN_EXPLANATIONS = {
    "grievances": "High grievance volume is increasing the predicted delay risk.",
    "grievance_growth_rate": "Rapid growth in grievances is increasing risk.",
    "consultation_progress_pct": "Low consultation progress is increasing the risk of a stage delay.",
    "compensation_pending_pct": "A large share of pending compensation is increasing delay risk.",
    "legal_disputes": "Active legal disputes are increasing delay risk.",
    "document_completeness_pct": "Incomplete documentation is increasing processing risk.",
    "land_records_match_pct": "Land-record mismatches are increasing verification risk.",
    "utility_conflicts": "Unresolved utility conflicts may delay possession or construction.",
    "affected_landowners": "Large number of affected landowners increases coordination complexity.",
    "affected_area": "Larger affected area increases acquisition complexity.",
    "notification_age_days": "Longer time since notification without progress increases delay risk.",
    "pending_clearances": "Pending clearances are blocking stage progression.",
    "historical_regional_delay_rate": "Historical delays in this region increase baseline risk.",
    "historical_stage_delay_rate": "This stage has historically high delay rates.",
    "stage": "Current acquisition stage influences delay likelihood.",
    "state": "State-specific administrative patterns affect risk.",
    "project_size": "Project size influences execution complexity.",
}

def human_explanation_for(feature: str, contribution: float) -> str:
    base = HUMAN_EXPLANATIONS.get(feature, f"{feature} is influencing risk.")
    if contribution < 0:
        # invert to reduce language
        return base.replace("increasing", "reducing").replace("High", "Lower").replace("Large", "Lower")
    return base

def direction_for(contribution: float) -> str:
    return "increases risk" if contribution >= 0 else "reduces risk"
