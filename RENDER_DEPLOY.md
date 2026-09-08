# Render Deploy — Quick Procedure

**Repo:** https://github.com/raghukanna77/Landora
**Blueprint:** `render.yaml` (databases + bhoomi-api + bhoomi-frontend)

## Option A — Blueprint (Recommended, 1-click)
1. GitHub: push latest (already done `78aeee2` + Render fixes)
   ```bash
   git push origin main
   ```
2. Render: https://dashboard.render.com → **New** → **Blueprint** → Connect `Landora` → **Apply**
   - Creates `bhoomi-db` (Postgres Free), `bhoomi-api` (Python), `bhoomi-frontend` (Static)
3. Wait 3-4 min → `bhoomi-api` logs: `Seed complete` → `bhoomi-frontend` built `dist`
4. Open:
   - Frontend: `https://bhoomi-frontend.onrender.com`
   - API: `https://bhoomi-api.onrender.com/health`, `/docs`
5. Test: Landing → Raise Complaint (no login) → BD-2026-PB-XXXXXX → Login admin/demo123 → Dashboard

If names `bhoomi-api` already taken, Render suffixes with random hash — use actual URLs shown in Dashboard.

## Option B — Manual (if Blueprint not used)
**Backend:**
- New → Web Service → Landora, Root `backend`, Runtime Python, Build `pip install -r requirements.txt`, Start `bash start.sh`, Health `/health`
- Env: `DATABASE_URL` (from your manually created Postgres), `JWT_SECRET` generate, `CORS_ORIGINS=https://<your-frontend>.onrender.com`, `FRONTEND_URL=https://<your-frontend>.onrender.com`

**Frontend:**
- New → Static Site → Landora, Root `frontend`, Build `npm ci && VITE_API_URL=https://<your-backend>.onrender.com npm run build`, Publish `dist`, Rewrite `/* -> /index.html`, Env `VITE_API_URL=https://<your-backend>.onrender.com`

## Env Vars Checklist
**Backend:**
```
DATABASE_URL=postgresql://... (fromDatabase)
JWT_SECRET=<generated>
CORS_ORIGINS=https://bhoomi-frontend.onrender.com
FRONTEND_URL=https://bhoomi-frontend.onrender.com
```
**Frontend:**
```
VITE_API_URL=https://bhoomi-api.onrender.com
```

## After Deploy — Fix CORS if needed
If browser console shows CORS blocked:
- Backend → Environment → add `CORS_ORIGINS` + `FRONTEND_URL` = your actual frontend URL → **Manual Deploy** → **Clear build cache & deploy**

## Verify
```bash
curl https://bhoomi-api.onrender.com/health  # {"status":"ONLINE"}
curl https://bhoomi-api.onrender.com/openapi.json | grep /api/voice/query
# Frontend should show: See the delay before it happens.
```

Full details: `docs/deployment.md`
