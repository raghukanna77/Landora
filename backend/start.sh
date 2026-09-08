#!/bin/bash
set -e
# Render provides $PORT, fallback to 8000
PORT=${PORT:-8000}
echo "Starting Bhoomi-Drishti on port $PORT"
echo "DATABASE_URL: ${DATABASE_URL:0:30}..."
# Run migrations/seed is handled in lifespan, but ensure model artifacts exist
if [ ! -f "./ml/artifacts/model.joblib" ]; then
  echo "Model not found, training..."
  python -m app.ml.train || echo "Training failed, will train on startup"
fi
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
