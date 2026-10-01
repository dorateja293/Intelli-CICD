"""
Kafka Producer/Consumer Module

Provides Kafka producer and consumer utilities for inter-service communication.
"""

import json
from functools import lru_cache
from typing import Any, Optional

import structlog

try:
    from confluent_kafka import Consumer, KafkaError, KafkaException, Producer
    HAS_KAFKA = True
except ImportError:
    HAS_KAFKA = False
    Consumer = None
    KafkaError = None
    KafkaException = Exception
    Producer = None
from pydantic import BaseModel

from config.settings import get_settings

logger = structlog.get_logger()
settings = get_settings()


class DummyProducer:
    """In-memory dummy producer when Kafka is not available."""
    def produce(self, *args, **kwargs):
        pass
    def poll(self, *args, **kwargs):
        pass
    def flush(self, *args, **kwargs):
        return 0


class DummyConsumer:
    """In-memory dummy consumer when Kafka is not available."""
    def __init__(self, *args, **kwargs):
        pass
    def subscribe(self, *args, **kwargs):
        pass
    def poll(self, *args, **kwargs):
        return None
    def commit(self, *args, **kwargs):
        pass
    def close(self):
        pass
    def list_topics(self):
        return {}


def delivery_callback(err: Optional[Any], msg: Any) -> None:
    """Callback for Kafka message delivery."""
    if err:
        logger.error("Kafka delivery failed", error=str(err), topic=getattr(msg, "topic", lambda: "")())
    else:
        logger.debug(
            "Kafka message delivered",
            topic=getattr(msg, "topic", lambda: "")(),
            partition=getattr(msg, "partition", lambda: 0)(),
            offset=getattr(msg, "offset", lambda: 0)(),
        )


@lru_cache
def get_producer() -> Any:
    """Get cached Kafka producer instance."""
    if not HAS_KAFKA or not Producer:
        return DummyProducer()
    try:
        config = {
            "bootstrap.servers": settings.kafka.bootstrap_servers,
            "client.id": f"{settings.service.service_name}-producer",
            "acks": "all",
            "retries": 5,
            "retry.backoff.ms": 500,
            "compression.type": "lz4",
            "linger.ms": 5,
            "batch.size": 16384,
        }
        return Producer(config)
    except Exception as e:
        logger.warning("Kafka producer init failed, falling back to dummy", error=str(e))
        return DummyProducer()


def create_consumer(group_id: str, topics: list[str]) -> Any:
    """Create a Kafka consumer for the given group and topics."""
    if not HAS_KAFKA or not Consumer:
        return DummyConsumer()
    try:
        config = {
            "bootstrap.servers": settings.kafka.bootstrap_servers,
            "group.id": group_id,
            "client.id": f"{settings.service.service_name}-{group_id}",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "max.poll.interval.ms": 300000,
            "session.timeout.ms": 45000,
            "heartbeat.interval.ms": 3000,
        }
        consumer = Consumer(config)
        consumer.subscribe(topics)
        return consumer
    except Exception as e:
        logger.warning("Kafka consumer init failed, falling back to dummy", error=str(e))
        return DummyConsumer()


async def publish_message(
    topic: str,
    key: str,
    value: dict[str, Any] | BaseModel,
    headers: Optional[dict[str, str]] = None,
) -> None:
    """Publish a message to Kafka topic."""
    producer = get_producer()

    # Serialize value
    if isinstance(value, BaseModel):
        value_bytes = value.model_dump_json().encode("utf-8")
    else:
        value_bytes = json.dumps(value).encode("utf-8")

    # Convert headers
    kafka_headers = [(k, v.encode("utf-8")) for k, v in (headers or {}).items()]
    kafka_headers.append(("content-type", b"application/json"))

    producer.produce(
        topic=topic,
        key=key.encode("utf-8"),
        value=value_bytes,
        headers=kafka_headers,
        callback=delivery_callback,
    )
    producer.poll(0)  # Trigger delivery callbacks


def flush_producer(timeout: float = 10.0) -> None:
    """Flush pending producer messages."""
    producer = get_producer()
    remaining = producer.flush(timeout)
    if remaining > 0:
        logger.warning("Kafka flush incomplete", remaining_messages=remaining)


class KafkaConsumerLoop:
    """Async Kafka consumer loop with graceful shutdown."""

    def __init__(
        self,
        group_id: str,
        topics: list[str],
        poll_timeout: float = 1.0,
    ):
        self.consumer = create_consumer(group_id, topics)
        self.poll_timeout = poll_timeout
        self._running = False

    async def start(self, handler: Any) -> None:
        """Start consuming messages."""
        self._running = True
        logger.info("Kafka consumer started", group=self.consumer.list_topics())

        while self._running:
            try:
                msg = self.consumer.poll(timeout=self.poll_timeout)
                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    raise KafkaException(msg.error())

                # Process message
                await handler(msg)

                # Commit offset after successful processing
                self.consumer.commit(message=msg)

            except KafkaException as e:
                logger.error("Kafka error", error=str(e))
            except Exception as e:
                logger.error("Message processing error", error=str(e))

    def stop(self) -> None:
        """Stop the consumer loop."""
        self._running = False
        self.consumer.close()
        logger.info("Kafka consumer stopped")


# Topic names from settings
TOPIC_PIPELINE_TRIGGER = settings.kafka.topic_pipeline_trigger
TOPIC_JOB_QUEUE = settings.kafka.topic_job_queue
TOPIC_JOB_EVENTS = settings.kafka.topic_job_events
TOPIC_LOG_STREAM = settings.kafka.topic_log_stream
TOPIC_LOG_ERRORS = settings.kafka.topic_log_errors
TOPIC_ALERTS = settings.kafka.topic_alerts
TOPIC_SECURITY_RESULTS = settings.kafka.topic_security_results
