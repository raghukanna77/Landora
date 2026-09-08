# Architecture
Layers: Frontend (React) → FastAPI → Services (risk, precedent, grievance, simulator, recommendation) → ML (LightGBM+Calibrated) → NLP (spaCy baseline) → GIS (Haversine/PostGIS-ready) → Voice (BHASHINI/Demo) → DB (SQLAlchemy, PostGIS geometry field). See README for loop.
