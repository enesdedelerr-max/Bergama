/**
 * Public product API TypeScript projections for Sprint 15 WS1.
 * Match frozen Sprint 14 public DTO families only.
 * Private ADE attestation payload fields are intentionally absent.
 */

export type ProductErrorResponse = {
  code: string;
  message: string;
  request_id: string;
  details?: Record<string, unknown> | null;
};

export type AdeProductProvenanceRead = {
  policy_version_id: string;
  identity_specification_id: string;
  provenance_specification_id: string;
  acceptance_specification_id: string;
  digest_method_id: string;
  derivation_attribution_id: string;
  as_of: string;
  human_review_output_id?: string | null;
  human_review_policy_version_id?: string | null;
  human_review_identity_specification_id?: string | null;
  human_review_provenance_specification_id?: string | null;
  human_review_config_fingerprint?: string | null;
  human_review_input_fingerprint?: string | null;
  recorded_attestation_fingerprint?: string | null;
  config_fingerprint: string;
  evidence_fingerprint: string;
};

export type AdeProductSnapshotRead = {
  outcome_kind: string;
  policy_version_id: string;
  as_of: string;
  reason_family: string;
  decision_id?: string | null;
  human_review_output_id?: string | null;
  provenance: AdeProductProvenanceRead;
  detail?: string | null;
};

/** Opaque/untrusted Human Review attestation payload (string only). */
export type HumanReviewRecordedAttestation = {
  recorded_payload: string;
};

export type DashboardPresentationOutput = {
  dashboard_output_id: string;
  policy_version_id: string;
  ordering_preservation_policy_id: string;
  presentation_selection_policy_id: string;
  as_of: string;
  records: readonly unknown[];
  provenance: Record<string, unknown>;
};

export type HumanReviewOutput = {
  human_review_output_id: string;
  policy_version_id: string;
  ordering_preservation_policy_id: string;
  presentation_preservation_policy_id: string;
  human_attestation_policy_id: string;
  identity_specification_id: string;
  provenance_specification_id: string;
  history_specification_id: string;
  as_of: string;
  dashboard_output_id: string;
  records: readonly unknown[];
  attestation: HumanReviewRecordedAttestation;
  provenance: Record<string, unknown>;
  history: Record<string, unknown>;
};

export type IntelligenceRunRead = {
  run_id: string;
  pipeline_fingerprint?: string | null;
  as_of?: string | null;
  persisted_at: string;
  snapshot_contract_version: string;
  persistence_schema_version: string;
  age_seconds: number;
  outcome: string;
  failed_stage?: string | null;
  failure_error_type?: string | null;
  failure_detail?: string | null;
  bindings?: Record<string, unknown> | null;
  provenance: Record<string, unknown>;
  stage_presence: Record<string, string>;
  dashboard?: DashboardPresentationOutput | null;
  human_review?: HumanReviewOutput | null;
  ade?: AdeProductSnapshotRead | null;
};

export type IntelligenceRunDashboardRead = {
  run_id: string;
  dashboard: DashboardPresentationOutput;
};

export type IntelligenceRunHumanReviewRead = {
  run_id: string;
  human_review: HumanReviewOutput;
};

export type IntelligenceRunAdeRead = {
  run_id: string;
  ade: AdeProductSnapshotRead;
};

export type BootstrapTokenResponse = {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
};
