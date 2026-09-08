def generate_recommendations(project, explanations, risk_prob):
    recs=[]
    # map driver -> action
    # Check drivers
    feat_set = {e["feature"]: e["contribution"] for e in explanations}
    # Priority logic
    def add(action, owner, priority, reason, reduction):
        recs.append({"action":action,"owner_role":owner,"priority":priority,"reason":reason,"predicted_risk_reduction":reduction})
    # Grievance + consultation
    if project.grievances>15 or project.consultation_progress_pct<60:
        red = min(0.18, (1-project.consultation_progress_pct/100)*0.25)
        add("Conduct targeted consultation/hearing","LAND_ACQUISITION_OFFICER","HIGH","Low consultation progress + high grievance intensity",round(red,3))
    if project.compensation_pending_pct>40:
        red = min(0.15, project.compensation_pending_pct/100*0.2)
        add("Prioritize compensation verification/payment worklist","REVENUE_OFFICER","HIGH","Large share of pending compensation",round(red,3))
    if project.legal_disputes>3:
        add("Create legal reconciliation worklist","LEGAL_OFFICER","HIGH","Active legal disputes",0.10)
    if project.document_completeness_pct<80:
        add("Close missing-document checklist","PROJECT_MANAGER","MEDIUM","Incomplete documentation",0.08)
    if project.land_records_match_pct<80:
        add("Initiate land-record reconciliation","REVENUE_OFFICER","MEDIUM","Land-record mismatches",0.07)
    if project.utility_conflicts>2:
        add("Coordinate utility shifting plan","PROJECT_MANAGER","MEDIUM","Unresolved utility conflicts",0.06)
    if project.pending_clearances>2:
        add("Expedite pending clearances coordination","PROJECT_MANAGER","MEDIUM","Pending clearances blocking stage",0.05)
    # fallback
    if not recs:
        add("Schedule periodic review and stakeholder check-in","PROJECT_MANAGER","LOW","No major driver — preventive monitoring",0.03)
    # sort by predicted reduction desc then priority
    order={"HIGH":3,"MEDIUM":2,"LOW":1}
    recs_sorted=sorted(recs, key=lambda x: (x["predicted_risk_reduction"], order[x["priority"]]), reverse=True)
    return recs_sorted[:5]
