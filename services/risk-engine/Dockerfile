FROM python:3.11-slim

# PIP_*: belt-and-braces for any stray pip call, not just the one below
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# fixed uid (k8s runAsNonRoot can verify), no home dir, no login shell
RUN useradd -u 10001 -M -s /usr/sbin/nologin appuser

# --chown at copy time: replaces `chown -R`, which doubled app+artifacts
# bytes into an extra image layer
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser artifacts ./artifacts

USER appuser

# build-time smoke test, running AS appuser: imports work, permissions work,
# and IF a forecaster.pkl is present it must actually load and forecast
# (the v2 dict.predict_proba crash fails the BUILD, not prod).
# compileall: precompiled .pyc -> faster cold start (env var only blocks
# runtime writes; precompiled files still load).
RUN python -m compileall -q app && \
    python -c "from pathlib import Path; from app.forecast import load_model, forecast; from app.schemas import ForecastRequest; assert not Path('artifacts/forecaster.pkl').exists() or load_model(), 'artifact present but rejected'; forecast(ForecastRequest(case_id='build-smoke', score_history=[0.3, 0.5, 0.7])); print('smoke ok')"

EXPOSE 8200

# 127.0.0.1 not 'localhost' (localhost can resolve to ::1 while uvicorn
# binds 0.0.0.0/IPv4 -> flapping healthchecks). start-period covers model
# load. urlopen gets its own timeout + a real status check.
HEALTHCHECK --start-period=20s --interval=15s --timeout=3s --retries=3 \
  CMD python -c "import sys, urllib.request as u; sys.exit(0 if u.urlopen('http://127.0.0.1:8200/healthz', timeout=2).status == 200 else 1)"

# one worker on purpose: metrics counters + fusion noise cache are
# per-process -> scale with replicas, not --workers, or /metrics lies.
# --no-access-log: the middleware already logs every request with an id.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8200", "--no-access-log"]
