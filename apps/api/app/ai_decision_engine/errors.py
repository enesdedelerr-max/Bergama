"""Typed AI Decision Engine Foundation failures."""

from __future__ import annotations


class AdeError(Exception):
    code = "ai_decision_engine.error"

    def __init__(self, message: str | None = None, *, detail: str | None = None) -> None:
        super().__init__(message or self.code)
        self.detail = detail


class AdeValidationError(AdeError):
    code = "ai_decision_engine.validation_failed"


class AdeUnauthorizedInputError(AdeValidationError):
    code = "ai_decision_engine.unauthorized_input"


class AdeUnsupportedPolicyError(AdeValidationError):
    code = "ai_decision_engine.unsupported_policy"


class AdeModelParticipationError(AdeValidationError):
    code = "ai_decision_engine.model_participation_unauthorized"


class AdeReplayInequalityError(AdeError):
    code = "ai_decision_engine.replay_inequality"
