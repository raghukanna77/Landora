# BHOOMI-DRISHTI — AI-Powered Predictive Land Acquisition Delay Intelligence

From reactive monitoring to proactive land-governance intelligence.

> Predict the delay. Understand the reason. Test the intervention. Take the action. Measure the outcome. Learn for the next project.

**DEMO DATA — SYNTHETIC / CALIBRATED** — All data is synthetic, not official government records. AI-assisted decision support — predicted risk — human-in-the-loop — prototype.

**Deploy to Render:** See [`RENDER_DEPLOY.md`](./RENDER_DEPLOY.md) and [`render.yaml`](./render.yaml) — Blueprint `bhoomi-db` + `bhoomi-api` + `bhoomi-frontend` — one-click deploy.

**Live after Render:** Frontend `https://bhoomi-frontend.onrender.com` + API `https://bhoomi-api.onrender.com/health`

## Architecture
Existing systems (Bhoomi Rashi, PM GatiShakti, DILRMP, NHAI, State Revenue) → Digital records → **BHOOMI-DRISHTI Predictive Intelligence Layer** → Officer Action

Loop: **PREDICT → EXPLAIN → SIMULATE → RECOMMEND → ACT → TRACK → LEARN → PREDICT AGAIN**

Stack: React+TS+Vite, FastAPI+SQLAlchemy, SQLite (PostGIS-ready), LightGBM, SHAP TreeExplainer, spaCy-baseline NLP, Leaflet GIS, JWT RBAC, Docker.

## Quick Start

### Backend
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
# train + seed
PYTHONPATH=backend python3 backend/seed.py
# run
PYTHONPATH=backend uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
# docs: http://127.0.0.1:8000/docs
```

### Frontend
```bash
cd frontend && npm install && npm run build
npx vite --host 127.0.0.1 --port 5173
# or: npm run dev (if vite installed)
```

### Docker
```bash
docker compose up --build
# frontend http://localhost:5173  backend http://localhost:8000/docs
```

## Demo Credentials (DEMO ONLY)
- admin / demo123 (ADMIN)
- officer / demo123 (STATE_OFFICER Punjab)
- reviewer / demo123 (NATIONAL_REVIEWER)
- district / demo123 (DISTRICT_OFFICER Amritsar)

## 5-Min Demo Script
1. Login admin/demo123
2. Dashboard: "live predictive command centre"
3. Open NH-48 Expansion Package A (PRJ-101) → SIA HIGH 94%
4. WHY → low consultation, high grievances, legal disputes
5. Precedents → similar 87% Punjab cases
6. Simulator → 42%→75% consultation → risk 94%→54%
7. Recommendations → Targeted consultation (LAND_ACQUISITION_OFFICER)
8. Grievances → "Our compensation..." → NEGATIVE/COMPENSATION/HIGH
9. Voice → English/Hindi/Tamil briefing
10. Accept recommendation → Record outcome "Consultation completed"
11. Outcomes → Queued for retraining

## API Overview
Auth: POST /api/auth/login, GET /api/auth/me  
Dashboard: GET /api/dashboard/summary|stage-risk|state-risk|heatmap|alerts  
Projects: GET/POST /api/projects, GET /api/projects/{id}  
Risk: GET /api/projects/{id}/risk, POST /api/projects/{id}/predict, GET /api/projects/{id}/explanation  
Precedents: GET /api/projects/{id}/precedents  
Grievances: POST /api/grievances, POST /api/grievances/analyze, GET /api/projects/{id}/grievances  
Simulator: POST /api/simulation/counterfactual  
Recommendations: GET /api/projects/{id}/advisory, POST /api/recommendations/{id}/accept|reject|defer  
Outcomes: POST /api/outcomes, GET /api/projects/{id}/outcomes  
Model: GET /api/model/status|metrics, GET /api/retraining/queue, POST /api/model/train|validate|approve  
Voice: POST /api/voice/briefing  
Ingestion: POST /api/ingestion/csv  
Health: GET /health, /ready, /metrics, /docs

## Known Limitations
- Synthetic data, demo auth, mock government adapters, demo voice, prototype ML (ROC ~0.62), simplified NLP, SQLite fallback, no real BHASHINI keys, no production hardening.

See docs/ for architecture, api.md, model-card, security, deployment, integrations, demo-script, limitations.
