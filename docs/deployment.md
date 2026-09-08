# Deployment — Render

## Architecture for Render
- **bhoomi-db** — Managed PostgreSQL (Render) `bhoomi` — fallback Text geometry if PostGIS unavailable
- **bhoomi-api** — Python Web Service (`backend/`, `start.sh`, `PORT`, `/health`)
- **bhoomi-frontend** — Static Site (`frontend/dist`, SPA rewrite)

`render.yaml` is a Blueprint — connect GitHub repo and Render provisions all three.

## Why These Changes for Render
- `DATABASE_URL` fix: Render gives `postgres://` → app converts to `postgresql://`
- `psycopg2-binary` + `gunicorn` added to `requirements.txt`
- `backend/app/database.py` handles `pool_pre_ping` + optional `CREATE EXTENSION postgis` (no-fail)
- `backend/app/config.py` adds `PORT`, `FRONTEND_URL`, `get_database_url()`, `get_cors_origins()` (reads `CORS_ORIGINS` + `FRONTEND_URL`)
- `backend/app/main.py` adds `lifespan` that auto-creates tables + trains/seeds if empty (fixes ephemeral FS), serves `static/` if present, `CORS` from `settings.get_cors_origins()`
- `backend/start.sh` uses `$PORT` (Render injects)
- `frontend/src/services/api.ts` uses `import.meta.env.VITE_API_URL` (fallback `''`)
- `ml/artifacts/*` committed for fast cold start (no 60s training on first boot)
- `render.yaml` uses `databases:` + `services:` with `env: python` / `env: static`

## One-Click Blueprint Deploy
1. Push to GitHub (`main` branch)
2. Render Dashboard → **New** → **Blueprint** → Connect `https://github.com/raghukanna77/Landora` → **Apply**
3. Render creates `bhoomi-db`, `bhoomi-api`, `bhoomi-frontend`
4. Wait ~3-4 min: `bhoomi-api` build `pip install` → `bash start.sh` → health `/health` → seed 620 projects
5. Note URLs:
   - API: `https://bhoomi-api.onrender.com` + `/docs`, `/health`
   - Frontend: `https://bhoomi-frontend.onrender.com`
6. If frontend shows CORS error, set env vars (below), trigger **Manual Deploy** → **Clear build cache & deploy**

## Manual Deploy (without Blueprint)
If Blueprint not used, create manually:

### 1. Database
- Render → **New** → **PostgreSQL** → Name `bhoomi-db`, Region `Singapore`, Plan Free → Create
- Copy **Internal Database URL** and **External Database URL**

### 2. Backend Web Service
- **New** → **Web Service** → Connect Landora → Root Directory `backend`
- Runtime `Python`, Build `pip install -r requirements.txt`, Start `bash start.sh`, Health ` /health`
- Vars:
  ```
  PYTHON_VERSION=3.11.9
  DATABASE_URL=<Internal Database URL from above>  # or External for local test
  JWT_SECRET=<generate>
  CORS_ORIGINS=https://bhoomi-frontend.onrender.com,http://localhost:5173
  FRONTEND_URL=https://bhoomi-frontend.onrender.com
  DEMO_MODE=true
  ```
- Deploy → logs should show `Seed complete` and `Uvicorn running on 0.0.0.0:$PORT`

### 3. Frontend Static Site
- **New** → **Static Site** → Connect Landora → Root `frontend`
- Build `npm ci && VITE_API_URL=https://bhoomi-api.onrender.com npm run build`
- Publish `dist`, Rewrite `/* -> /index.html`
- Env `VITE_API_URL=https://bhoomi-api.onrender.com`
- Deploy → open `https://bhoomi-frontend.onrender.com` → Landing → Complaint without login → Track

## Environment Variables
**Backend (`bhoomi-api`):**
| Key | Example | Notes |
|-----|---------|-------|
| `DATABASE_URL` | `postgresql://...` | From Render Postgres (auto via `fromDatabase`) |
| `JWT_SECRET` | `generateValue: true` | Or set strong random |
| `CORS_ORIGINS` | `https://bhoomi-frontend.onrender.com,http://localhost:5173` | Comma separated, must include frontend URL |
| `FRONTEND_URL` | `https://bhoomi-frontend.onrender.com` | Also added to CORS |
| `DEMO_MODE` | `true` |  |
| `BHASHINI_API_KEY` | `` | Empty → DemoVoiceProvider |

**Frontend (`bhoomi-frontend`):**
| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://bhoomi-api.onrender.com` |

## Local Production Test (before pushing)
```bash
# Backend with PORT + Postgres fallback (sqlite for local)
PORT=10000 DATABASE_URL=sqlite:///./test.db PYTHONPATH=backend bash backend/start.sh
curl http://localhost:10000/health  # should be ONLINE after ~30s seed if DB empty
# Frontend with backend URL
VITE_API_URL=https://bhoomi-api.onrender.com npm --prefix frontend run build
npx --prefix frontend vite preview --port 5173  # serves dist
```

## Render Free Tier Notes
- **Spin-down:** Free services spin down after 15m idle → first request takes 30-60s (cold start includes seed if DB empty, but artifacts committed so ~10s)
- **Postgres free:** 90 days, then expires → backup or recreate; PostGIS not guaranteed (app falls back)
- **Logs:** Dashboard → Service → Logs → filter `Seed complete` to verify seed
- **Health check:** Render calls `/health` every few seconds — must return 200 within startup timeout (increased by committing artifacts)

## Updating
```bash
git add . && git commit -m "feat: render ready" && git push origin main
# If Blueprint autoDeploy false, Dashboard → Manual Deploy → Deploy latest commit
# If autoDeploy true, push auto-triggers
```

## Alternative: Single Docker Service
If you prefer one service (API + static), build `Dockerfile.fullstack` that copies `frontend/dist` to `backend/static` and `app.main` mounts `/app`. Not needed for current Blueprint; use two services as above.

## Troubleshooting
- **CORS error in browser:** `CORS_ORIGINS` missing frontend URL → add to backend env and redeploy
- **Frontend shows no data:** `VITE_API_URL` wrong or backend down → check `https://bhoomi-api.onrender.com/health`
- **Database connection error:** `DATABASE_URL` uses `postgres://` → app auto-fixes, but ensure `psycopg2-binary` in requirements
- **500 on first load:** Check logs for `Seed complete` — if DB empty and artifacts missing, training takes 60s — wait and retry
- **Model not found:** `ml/artifacts/model.joblib` committed, so training skipped on cold start
