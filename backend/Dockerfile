FROM python:3.11-slim
# libgomp required for LightGBM + SHAP
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
# Build Context is repo root (.) — see Render: Root Directory backend, Docker Build Context .
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/. ./
COPY ml ./ml
RUN chmod +x start.sh
EXPOSE 8000
CMD ["bash","start.sh"]
