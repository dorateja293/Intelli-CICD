FROM python:3.12-slim

WORKDIR /app

# System deps for asyncpg / bcrypt
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-create model directory so the app doesn't crash if no model exists yet
RUN mkdir -p ml-engine/models

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
