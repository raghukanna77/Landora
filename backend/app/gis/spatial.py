import math

def haversine(lat1, lon1, lat2, lon2):
    R=6371.0
    dlat=math.radians(lat2-lat1)
    dlon=math.radians(lon2-lon1)
    a=math.sin(dlat/2)**2+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    c=2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R*c

def similarity_score(project, candidate):
    # normalized weighted similarity 0-1
    # smaller distance + similar features + same state/district/stage
    score=0.0
    # categorical matches
    if project.state==candidate.state: score+=0.15
    if project.district==candidate.district: score+=0.10
    if project.current_stage==candidate.current_stage: score+=0.15
    if project.project_size==candidate.project_size: score+=0.05
    # numeric closeness (inverse normalized distance)
    def closeness(a,b,scale):
        return max(0, 1 - abs(a-b)/scale)
    score+=0.08*closeness(project.affected_landowners, candidate.affected_landowners, 200)
    score+=0.07*closeness(project.grievances, candidate.grievances, 40)
    score+=0.07*closeness(project.compensation_pending_pct, candidate.compensation_pending_pct, 100)
    score+=0.07*closeness(project.consultation_progress_pct, candidate.consultation_progress_pct, 100)
    score+=0.05*closeness(project.legal_disputes, candidate.legal_disputes, 10)
    score+=0.05*closeness(project.land_records_match_pct, candidate.land_records_match_pct, 100)
    # spatial proximity component (within 100km)
    if project.latitude and project.longitude and candidate.latitude and candidate.longitude:
        dist=haversine(project.latitude, project.longitude, candidate.latitude, candidate.longitude)
        score+=0.08*max(0, 1 - dist/300)
    # also consultation etc.
    score+=0.05*closeness(project.document_completeness_pct, candidate.document_completeness_pct,100)
    score+=0.03*closeness(project.utility_conflicts, candidate.utility_conflicts,10)
    return min(1.0, score)

def pattern_for(project):
    parts=[]
    if project.grievances>25: parts.append("High grievances")
    if project.consultation_progress_pct<50: parts.append("low consultation")
    if project.legal_disputes>5: parts.append("legal disputes")
    if project.compensation_pending_pct>50: parts.append("compensation backlog")
    if project.land_records_match_pct<75: parts.append("land-record mismatch")
    if not parts: parts=["Moderate risk pattern"]
    return " + ".join(parts[:3])
