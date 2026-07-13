"""Kafka infrastructure adapters."""

from __future__ import annotations

from app.infrastructure.kafka.runtime import KafkaRuntime, build_kafka_runtime

__all__ = ["KafkaRuntime", "build_kafka_runtime"]
