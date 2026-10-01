# =================================================
# Base Python Image for All Services
# =================================================
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# =================================================
# Dependencies Stage
# =================================================
FROM base as dependencies

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# =================================================
# Webhook Service
# =================================================
FROM dependencies as webhook-service

COPY config/ ./config/
COPY shared/ ./shared/
COPY services/webhook/ ./services/webhook/

EXPOSE 8001

CMD ["uvicorn", "services.webhook.main:app", "--host", "0.0.0.0", "--port", "8001"]

# =================================================
# Pipeline Orchestrator
# =================================================
FROM dependencies as orchestrator-service

COPY config/ ./config/
COPY shared/ ./shared/
COPY services/orchestrator/ ./services/orchestrator/

EXPOSE 8002

CMD ["uvicorn", "services.orchestrator.main:app", "--host", "0.0.0.0", "--port", "8002"]

# =================================================
# Worker Agent
# =================================================
FROM dependencies as worker-service

# Worker needs docker CLI for container execution
RUN apt-get update && apt-get install -y --no-install-recommends \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

COPY config/ ./config/
COPY shared/ ./shared/
COPY services/worker/ ./services/worker/

CMD ["python", "-m", "services.worker.main"]

# =================================================
# Log Processor
# =================================================
FROM dependencies as log-processor-service

COPY config/ ./config/
COPY shared/ ./shared/
COPY services/log_processor/ ./services/log_processor/

EXPOSE 8003

CMD ["uvicorn", "services.log_processor.main:app", "--host", "0.0.0.0", "--port", "8003"]

# =================================================
# Security Scanner
# =================================================
FROM dependencies as security-scanner-service

# Install security scanning tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin \
    && curl -sSfL https://raw.githubusercontent.com/gitleaks/gitleaks/main/scripts/install.sh | sh -s -- -b /usr/local/bin \
    && pip install --no-cache-dir semgrep \
    && rm -rf /var/lib/apt/lists/*

COPY config/ ./config/
COPY shared/ ./shared/
COPY services/security_scanner/ ./services/security_scanner/

EXPOSE 8004

CMD ["uvicorn", "services.security_scanner.main:app", "--host", "0.0.0.0", "--port", "8004"]

# =================================================
# Notification Service
# =================================================
FROM dependencies as notification-service

COPY config/ ./config/
COPY shared/ ./shared/
COPY services/notification/ ./services/notification/

EXPOSE 8005

CMD ["uvicorn", "services.notification.main:app", "--host", "0.0.0.0", "--port", "8005"]

# =================================================
# API Service
# =================================================
FROM dependencies as api-service

COPY config/ ./config/
COPY shared/ ./shared/
COPY services/api/ ./services/api/

EXPOSE 8000

CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# =================================================
# Log Analyzer (AI Engine)
# =================================================
FROM dependencies as log-analyzer-service

COPY config/ ./config/
COPY shared/ ./shared/
COPY ai/ ./ai/

EXPOSE 8006

CMD ["uvicorn", "ai.log_analyzer.main:app", "--host", "0.0.0.0", "--port", "8006"]
