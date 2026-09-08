import csv, io
from .base import BaseAdapter

REQUIRED = ["project_code","name","state","district","current_stage"]
VALID_STAGES=["Notification","SIA","Consent","Award","Compensation","Possession"]

class CSVAdapter(BaseAdapter):
    def validate(self, content: str) -> dict:
        reader=csv.DictReader(io.StringIO(content))
        rows=list(reader)
        total=len(rows)
        accepted=0
        rejected=0
        errors=[]
        seen=set()
        for i, r in enumerate(rows, start=2):
            if not r.get("project_code"):
                errors.append(f"Row {i}: missing project_code"); rejected+=1; continue
            if r["project_code"] in seen:
                errors.append(f"Row {i}: duplicate project_code {r['project_code']}"); rejected+=1; continue
            seen.add(r["project_code"])
            if r.get("current_stage") not in VALID_STAGES:
                errors.append(f"Row {i}: invalid stage {r.get('current_stage')}"); rejected+=1; continue
            try:
                lat=float(r.get("latitude") or 0)
                lon=float(r.get("longitude") or 0)
                if lat and not (-90<=lat<=90): raise ValueError
                if lon and not (-180<=lon<=180): raise ValueError
            except:
                errors.append(f"Row {i}: invalid coordinates"); rejected+=1; continue
            accepted+=1
        return {"total_rows":total,"accepted":accepted,"rejected":rejected,"errors":errors[:20]}
    def ingest(self, payload: dict) -> dict:
        return {"success": True, "message":"CSV ingested (demo)"}
