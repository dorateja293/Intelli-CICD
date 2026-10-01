"""Kafka module."""

from shared.kafka.producer import (
    TOPIC_ALERTS,
    TOPIC_JOB_EVENTS,
    TOPIC_JOB_QUEUE,
    TOPIC_LOG_ERRORS,
    TOPIC_LOG_STREAM,
    TOPIC_PIPELINE_TRIGGER,
    TOPIC_SECURITY_RESULTS,
    KafkaConsumerLoop,
    create_consumer,
    flush_producer,
    get_producer,
    publish_message,
)

__all__ = [
    "get_producer",
    "create_consumer",
    "publish_message",
    "flush_producer",
    "KafkaConsumerLoop",
    "TOPIC_PIPELINE_TRIGGER",
    "TOPIC_JOB_QUEUE",
    "TOPIC_JOB_EVENTS",
    "TOPIC_LOG_STREAM",
    "TOPIC_LOG_ERRORS",
    "TOPIC_ALERTS",
    "TOPIC_SECURITY_RESULTS",
]
