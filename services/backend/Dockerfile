# Multi-stage Docker build for FastAPI Backend
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Final runtime image
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
