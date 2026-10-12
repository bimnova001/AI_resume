# Backend: FastAPI + BGE-M3 + Qwen (CPU).
# NOTE: first start downloads ~4GB of models into /app/model_cache (keep the
# named volume). Image build needs a C++ toolchain for llama-cpp-python and
# pulls PyTorch (~1GB) — expect a big image and a slow first build.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Toolchain for llama-cpp-python wheel build
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app.py logger.py ./
COPY model/ ./model/

# Runtime dirs (overridden by compose volumes)
RUN mkdir -p /app/data /app/model_cache /app/uploads /app/logs

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/jobs/status', timeout=8)"

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
