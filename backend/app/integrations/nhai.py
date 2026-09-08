from .base import BaseAdapter
class NHAIAdapter(BaseAdapter):
    def validate(self, payload: dict) -> dict: return {"requires_credentials": True}
    def ingest(self, payload: dict) -> dict: return {"success": False, "message": "Integration requires authorized government API credentials."}
