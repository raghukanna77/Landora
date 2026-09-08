from fastapi import APIRouter, Depends, UploadFile, File
from ..auth.security import get_current_user
from ..models.user import User
from ..integrations.csv_adapter import CSVAdapter

router=APIRouter()

@router.post("/csv")
async def ingest_csv(file: UploadFile = File(...), user:User=Depends(get_current_user)):
    content=(await file.read()).decode()
    adapter=CSVAdapter()
    result=adapter.validate(content)
    return {"success":True,"data":result,"meta":{}}
@router.post("/validate")
async def validate(file: UploadFile = File(...), user:User=Depends(get_current_user)):
    content=(await file.read()).decode()
    adapter=CSVAdapter()
    result=adapter.validate(content)
    return {"success":True,"data":result,"meta":{}}
