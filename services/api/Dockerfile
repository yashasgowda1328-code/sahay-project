FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY services/api/requirements.txt ./services/api/requirements.txt
RUN pip install --no-cache-dir -r ./services/api/requirements.txt

COPY services/ ./services/
COPY ml/ ./ml/
COPY simulator/ ./simulator/
COPY protocols/ ./protocols/

ENV PYTHONPATH=/app:/app/services/api

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
