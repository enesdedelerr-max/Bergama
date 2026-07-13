"""Nested Kafka runtime settings (Issue #208A)."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class KafkaSettings(BaseModel):
    """Kafka client configuration. Disabled by default for local/test stability."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    bootstrap_servers: list[str] = Field(default_factory=list)
    client_id: str = Field(default="bergama-api", min_length=1)
    consumer_group_id: str = Field(default="bergama-api-runtime", min_length=1)
    request_timeout_seconds: float = Field(default=30.0, gt=0)
    session_timeout_seconds: float = Field(default=45.0, gt=0)
    heartbeat_interval_seconds: float = Field(default=3.0, gt=0)
    metadata_max_age_seconds: float = Field(default=300.0, gt=0)
    auto_offset_reset: Literal["earliest", "latest", "none"] = "earliest"
    enable_auto_commit: bool = False
    max_poll_records: int = Field(default=100, gt=0)
    consumer_enabled: bool = False
    producer_enabled: bool = True
    health_required: bool = False
    topic_prefix: str = ""
    acks: Literal["0", "1", "all"] = "all"
    # Topics the worker subscribes to when consumer_enabled (symbolic names).
    consumer_topics: list[str] = Field(
        default_factory=lambda: ["events"],
        description="KafkaTopic enum values, e.g. events, market-data.",
    )

    @field_validator("bootstrap_servers", mode="before")
    @classmethod
    def parse_bootstrap_servers(cls, value: object) -> object:
        if value is None:
            return []
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            if text.startswith("["):
                return value
            return [part.strip() for part in text.split(",") if part.strip()]
        return value

    @field_validator("client_id", "consumer_group_id")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            msg = "value must be non-empty"
            raise ValueError(msg)
        return value.strip()

    @model_validator(mode="after")
    def validate_kafka_semantics(self) -> Self:
        if self.enable_auto_commit:
            msg = "BERGAMA_KAFKA__ENABLE_AUTO_COMMIT must be false (manual commit policy)"
            raise ValueError(msg)
        if self.heartbeat_interval_seconds >= self.session_timeout_seconds:
            msg = "heartbeat_interval_seconds must be < session_timeout_seconds"
            raise ValueError(msg)
        if self.enabled and not self.bootstrap_servers:
            msg = "BERGAMA_KAFKA__BOOTSTRAP_SERVERS must be non-empty when Kafka is enabled"
            raise ValueError(msg)
        if self.enabled and self.consumer_enabled and not self.consumer_topics:
            msg = "consumer_topics must be non-empty when consumer_enabled is true"
            raise ValueError(msg)
        return self

    def safe_summary(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "bootstrap_servers_configured": bool(self.bootstrap_servers),
            "bootstrap_server_count": len(self.bootstrap_servers),
            "client_id": self.client_id,
            "consumer_group_id": self.consumer_group_id,
            "consumer_enabled": self.consumer_enabled,
            "producer_enabled": self.producer_enabled,
            "health_required": self.health_required,
            "enable_auto_commit": self.enable_auto_commit,
            "topic_prefix": self.topic_prefix,
            "acks": self.acks,
        }
