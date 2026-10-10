import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import type {
  AdeProductSnapshotRead,
  HumanReviewOutput,
  IntelligenceRunAdeRead,
  IntelligenceRunDashboardRead,
  IntelligenceRunHumanReviewRead,
  IntelligenceRunRead,
  ProductErrorResponse,
} from "@/contracts/types/product-api";

describe("public product DTO projections", () => {
  it("covers the five frozen public families", () => {
    const error: ProductErrorResponse = {
      code: "x",
      message: "y",
      request_id: "r1",
    };
    const run: IntelligenceRunRead = {
      run_id: "00000000-0000-0000-0000-000000000001",
      persisted_at: "2026-01-01T00:00:00Z",
      snapshot_contract_version: "1",
      persistence_schema_version: "1",
      age_seconds: 0,
      outcome: "ok",
      provenance: {},
      stage_presence: {},
    };
    const dashboard: IntelligenceRunDashboardRead = {
      run_id: run.run_id,
      dashboard: {
        dashboard_output_id: "a".repeat(64),
        policy_version_id: "p",
        ordering_preservation_policy_id: "o",
        presentation_selection_policy_id: "s",
        as_of: "2026-01-01T00:00:00Z",
        records: [],
        provenance: {},
      },
    };
    const humanReview: IntelligenceRunHumanReviewRead = {
      run_id: run.run_id,
      human_review: {
        human_review_output_id: "b".repeat(64),
        policy_version_id: "p",
        ordering_preservation_policy_id: "o",
        presentation_preservation_policy_id: "pp",
        human_attestation_policy_id: "ha",
        identity_specification_id: "i",
        provenance_specification_id: "pr",
        history_specification_id: "h",
        as_of: "2026-01-01T00:00:00Z",
        dashboard_output_id: "c".repeat(64),
        records: [],
        attestation: { recorded_payload: "<script>opaque</script>" },
        provenance: {},
        history: {},
      } satisfies HumanReviewOutput,
    };
    const ade: IntelligenceRunAdeRead = {
      run_id: run.run_id,
      ade: {
        outcome_kind: "abstain",
        policy_version_id: "p",
        as_of: "2026-01-01T00:00:00Z",
        reason_family: "none",
        provenance: {
          policy_version_id: "p",
          identity_specification_id: "i",
          provenance_specification_id: "pr",
          acceptance_specification_id: "a",
          digest_method_id: "d",
          derivation_attribution_id: "da",
          as_of: "2026-01-01T00:00:00Z",
          config_fingerprint: "d".repeat(64),
          evidence_fingerprint: "e".repeat(64),
        },
      } satisfies AdeProductSnapshotRead,
    };
    expect(error.code).toBe("x");
    expect(dashboard.dashboard.dashboard_output_id).toHaveLength(64);
    expect(humanReview.human_review.attestation.recorded_payload).toContain(
      "opaque",
    );
    expect(ade.ade.outcome_kind).toBe("abstain");
    expect("recorded_attestation_payload" in ade.ade).toBe(false);
  });

  it("keeps private ADE attestation payload out of public type declarations", () => {
    const file = readFileSync(join(__dirname, "product-api.ts"), "utf8");
    expect(file).not.toMatch(
      /^\s*recorded_attestation_payload\s*[?:]/m,
    );
  });
});
