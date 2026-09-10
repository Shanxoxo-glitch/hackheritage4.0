# PS26094 scoring service - CPU-only image (~1.6 GB incl. torch-cpu, weights NOT baked unless HF_TOKEN given)
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    SCORING_MODELS_DIR=/models SCORING_DEVICE=cpu SCORING_WARM_ON_START=1 \
    HF_HUB_DISABLE_TELEMETRY=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=2

RUN apt-get update && apt-get install -y --no-install-recommends libsndfile1 libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Option A (default): weights are bind-mounted at runtime  ->  ./models:/models  (docker-compose.yml)
# Option B: bake weights at build time from the private HF repo:
#   docker build --build-arg HF_TOKEN=hf_xxx -t sih-scoring services/scoring
ARG HF_TOKEN=""
ARG SCORING_HF_REPO="Shota2811/ps26094-signals"
RUN if [ -n "$HF_TOKEN" ]; then python -c "from huggingface_hub import snapshot_download; \
    snapshot_download('$SCORING_HF_REPO', local_dir='/models', token='$HF_TOKEN')"; fi

EXPOSE 8100
HEALTHCHECK --interval=15s --timeout=5s --start-period=90s --retries=10 \
    CMD curl -fsS http://localhost:8100/healthz || exit 1
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]
