FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app

EXPOSE 8000

# init_db is idempotent (CREATE EXTENSION/TABLE IF NOT EXISTS): bij de eerste
# start bestaan de tabellen nog niet, en /ask zou dan 500 geven.
CMD ["sh", "-c", "python -c 'from app.db import init_db; init_db()' && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-2}"]
