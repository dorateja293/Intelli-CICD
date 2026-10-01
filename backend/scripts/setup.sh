#!/bin/bash
#
# Intelli-CI Setup Script
# Sets up the development environment and starts all services
#

set -e

echo "========================================"
echo "Intelli-CI Development Environment Setup"
echo "========================================"

# Check prerequisites
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "ERROR: $1 is required but not installed."
        exit 1
    fi
}

echo "Checking prerequisites..."
check_command docker
check_command docker-compose
check_command python3

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please review .env and update settings as needed."
fi

# Create Python virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate || source venv/Scripts/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -q -r requirements.txt

# Start infrastructure services
echo "Starting infrastructure services..."
docker-compose up -d postgres redis zookeeper kafka elasticsearch

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check PostgreSQL
echo "Checking PostgreSQL..."
until docker-compose exec -T postgres pg_isready -U intellici; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done

# Check Kafka
echo "Checking Kafka..."
until docker-compose exec -T kafka kafka-broker-api-versions --bootstrap-server localhost:9092; do
    echo "Waiting for Kafka..."
    sleep 2
done

# Create Kafka topics
echo "Creating Kafka topics..."
docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --create --if-not-exists --topic pipeline.trigger --partitions 20 --replication-factor 1
docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --create --if-not-exists --topic job.queue --partitions 20 --replication-factor 1
docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --create --if-not-exists --topic job.events --partitions 20 --replication-factor 1
docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --create --if-not-exists --topic log.stream --partitions 50 --replication-factor 1
docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --create --if-not-exists --topic log.errors --partitions 20 --replication-factor 1
docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --create --if-not-exists --topic alerts --partitions 10 --replication-factor 1
docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --create --if-not-exists --topic security.results --partitions 10 --replication-factor 1

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Create Elasticsearch index template
echo "Creating Elasticsearch index template..."
curl -X PUT "localhost:9200/_index_template/logs" -H 'Content-Type: application/json' -d'
{
  "index_patterns": ["logs-*"],
  "template": {
    "settings": {
      "number_of_shards": 3,
      "number_of_replicas": 1,
      "refresh_interval": "5s"
    },
    "mappings": {
      "properties": {
        "job_id": {"type": "keyword"},
        "pipeline_id": {"type": "keyword"},
        "repo_id": {"type": "keyword"},
        "line_number": {"type": "integer"},
        "content": {"type": "text"},
        "timestamp": {"type": "date"},
        "level": {"type": "keyword"},
        "is_error": {"type": "boolean"},
        "error_fingerprint": {"type": "keyword"},
        "stack_trace_group": {"type": "keyword"},
        "section": {"type": "keyword"}
      }
    }
  }
}'

echo ""
echo "========================================"
echo "Setup complete!"
echo "========================================"
echo ""
echo "To start all Intelli-CI services:"
echo "  docker-compose up"
echo ""
echo "Or start services individually for development:"
echo "  python -m services.api.main"
echo "  python -m services.webhook.main"
echo "  python -m services.orchestrator.main"
echo "  python -m services.worker.main"
echo "  python -m services.log_processor.main"
echo "  python -m services.security_scanner.main"
echo "  python -m services.notification.main"
echo "  python -m ai.log_analyzer.main"
echo ""
echo "API documentation: http://localhost:8000/docs"
echo ""
