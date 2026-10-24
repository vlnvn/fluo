# Local-only packaging candidate. External deployment is BLOCKED; see deployment runbook.
ARG NODE_IMAGE=node:22-bookworm-slim
ARG PYTHON_IMAGE=python:3.12-slim
FROM ${NODE_IMAGE} AS web
WORKDIR /build
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM ${PYTHON_IMAGE} AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 FLUO_RELEASE_MODE=local FLUO_DB_PATH=/app/.local/fluo.sqlite3
WORKDIR /app
COPY requirements-runtime.lock ./
RUN pip install --no-cache-dir -r requirements-runtime.lock && useradd -u 10001 -m fluo
COPY backend/ ./backend/
COPY run_fluo_v2.py run_fluo_ml_v1.py ./
COPY models/fluo_hgb_synthetic_v2.joblib ./models/
COPY data/original/fluo_sensor_stream.csv.gz data/original/fluo_episode_labels.csv ./data/original/
COPY --from=web /build/dist ./web/dist/
COPY --from=web /build/public/assets ./web/public/assets/
RUN mkdir -p /app/.local && chown -R 10001:10001 /app/.local
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/health/ready',timeout=3)"
CMD ["python","-m","uvicorn","backend.app:app","--host","0.0.0.0","--port","8000","--workers","1","--no-server-header","--timeout-keep-alive","10"]
