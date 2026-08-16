"""Human Review Policy Version v1 constants."""

from __future__ import annotations

POLICY_VERSION_V1 = "human-review.policy.v1"
ORDERING_PRESERVATION_POLICY_V1 = "preserve_dashboard_order.v1"
PRESENTATION_PRESERVATION_POLICY_V1 = "include_all_dashboard_presentation_records.v1"
HUMAN_ATTESTATION_POLICY_V1 = "explicit_human_attestation.recorded_input.v1"
IDENTITY_SPECIFICATION_V1 = "human-review.identity.v1"
PROVENANCE_SPECIFICATION_V1 = "human-review.provenance.v1"
HISTORY_SPECIFICATION_V1 = "human-review.history.v1"
DIGEST_METHOD_V1 = "canonical_payload_sha256_v1"
OUTPUT_COMPLETENESS_POLICY_V1 = "output_completeness.exactly_one_complete_output.v1"
REPLAY_EQUALITY_POLICY_V1 = "replay_equality.structural_complete.v1"

CANONICAL_UTC_CONVENTION_ID = "utc_aware_instant_v1"
CANONICAL_DECIMAL_CONVENTION_ID = "canonical_decimal_str_v1"

REQUIRED_UPSTREAM_DASHBOARD_POLICY_VERSION_ID = "dashboard.policy.v1"
REQUIRED_UPSTREAM_DASHBOARD_IDENTITY_SPECIFICATION_ID = "dashboard.identity.v1"
REQUIRED_UPSTREAM_DASHBOARD_PROVENANCE_SPECIFICATION_ID = "dashboard.provenance.v1"
