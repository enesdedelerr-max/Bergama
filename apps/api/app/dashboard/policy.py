"""Dashboard Policy Version v1 constants."""

from __future__ import annotations

POLICY_VERSION_V1 = "dashboard.policy.v1"
ORDERING_PRESERVATION_POLICY_V1 = "preserve_morning_briefing_order.v1"
PRESENTATION_SELECTION_POLICY_V1 = "include_all_morning_briefing_records.v1"
IDENTITY_SPECIFICATION_V1 = "dashboard.identity.v1"
PROVENANCE_SPECIFICATION_V1 = "dashboard.provenance.v1"
DIGEST_METHOD_V1 = "canonical_payload_sha256_v1"
OUTPUT_COMPLETENESS_POLICY_V1 = "output_completeness.exactly_one_complete_output.v1"
REPLAY_EQUALITY_POLICY_V1 = "replay_equality.structural_complete.v1"

CANONICAL_UTC_CONVENTION_ID = "utc_aware_instant_v1"
CANONICAL_DECIMAL_CONVENTION_ID = "canonical_decimal_str_v1"

REQUIRED_UPSTREAM_BRIEFING_POLICY_VERSION_ID = "morning-briefing.policy.v1"
REQUIRED_UPSTREAM_BRIEFING_IDENTITY_SPECIFICATION_ID = "morning-briefing.identity.v1"
REQUIRED_UPSTREAM_BRIEFING_PROVENANCE_SPECIFICATION_ID = "morning-briefing.provenance.v1"
