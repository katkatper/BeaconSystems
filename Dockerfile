FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    API_BIND_HOST=0.0.0.0 \
    API_PORT=8000 \
    API_WORKERS=1 \
    FORWARDED_ALLOW_IPS=127.0.0.1

WORKDIR /app

RUN addgroup --system --gid 10001 beacon \
    && adduser --system --uid 10001 --ingroup beacon --home /app beacon

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --requirement requirements.txt

COPY alembic.ini main.py global-bundle.pem ./
COPY ai_engine ./ai_engine
COPY config ./config
COPY database ./database
COPY integrations ./integrations
COPY migrations ./migrations
COPY models ./models
COPY routes ./routes
COPY schemas ./schemas
COPY security ./security
COPY services ./services
COPY scripts/start_production.py ./scripts/start_production.py

RUN chown -R beacon:beacon /app
USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('API_PORT','8000') + '/health', timeout=3)"]

CMD ["python", "scripts/start_production.py"]
