FROM python:3.12-slim

WORKDIR /app

# System deps for asyncpg / bcrypt / healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt backend-requirements.txt
RUN pip install --no-cache-dir -r backend-requirements.txt

COPY ml-engine/requirements.txt ml-requirements.txt
RUN pip install --no-cache-dir -r ml-requirements.txt

COPY . .

# Pre-create model directory so the app doesn't crash if no model exists yet
RUN mkdir -p ml-engine/models

ENV PYTHONPATH="/app/backend:/app:${PYTHONPATH}"

EXPOSE 8000

CMD ["uvicorn", "services.api.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
