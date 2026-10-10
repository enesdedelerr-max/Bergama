import { describe, expect, it, vi } from "vitest";
import {
  BOOTSTRAP_ONLY_MUTATION_PATH,
  createIntelligenceClient,
  INTELLIGENCE_CLIENT_METHODS,
} from "@/lib/api/intelligence-client";

describe("intelligence client", () => {
  it("exposes exactly six GET helpers plus bootstrap POST", () => {
    expect([...INTELLIGENCE_CLIENT_METHODS].sort()).toEqual(
      [
        "getLatestDashboardCapable",
        "getRunAde",
        "getRunByFingerprint",
        "getRunById",
        "getRunDashboard",
        "getRunHumanReview",
        "postBootstrapToken",
      ].sort(),
    );
    expect(BOOTSTRAP_ONLY_MUTATION_PATH).toBe("/api/v1/auth/token");
    const client = createIntelligenceClient({
      getAccessToken: () => null,
      getAuthGeneration: () => 0,
      reacquireOnce: async () => false,
      onForbidden: () => undefined,
      apiBaseUrl: "http://localhost:8000",
    });
    expect(typeof (client as { createRun?: unknown }).createRun).toBe(
      "undefined",
    );
    expect(typeof (client as { writeRun?: unknown }).writeRun).toBe("undefined");
  });

  it("calls the six frozen GET routes", async () => {
    const paths: string[] = [];
    const fetchImpl = vi.fn(async (url: string) => {
      paths.push(new URL(url).pathname);
      return new Response(
        JSON.stringify({
          run_id: "00000000-0000-0000-0000-000000000001",
          persisted_at: "2026-01-01T00:00:00Z",
          snapshot_contract_version: "1",
          persistence_schema_version: "1",
          age_seconds: 0,
          outcome: "ok",
          provenance: {},
          stage_presence: {},
          dashboard: {
            dashboard_output_id: "a".repeat(64),
            policy_version_id: "p",
            ordering_preservation_policy_id: "o",
            presentation_selection_policy_id: "s",
            as_of: "2026-01-01T00:00:00Z",
            records: [],
            provenance: {},
          },
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
            attestation: { recorded_payload: "text" },
            provenance: {},
            history: {},
          },
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
          },
        }),
        { status: 200 },
      );
    });
    const client = createIntelligenceClient({
      getAccessToken: () => "tok",
      getAuthGeneration: () => 1,
      reacquireOnce: async () => false,
      onForbidden: () => undefined,
      fetchImpl: fetchImpl as unknown as typeof fetch,
      apiBaseUrl: "http://localhost:8000",
    });
    const runId = "00000000-0000-0000-0000-000000000001";
    await client.getRunById(runId);
    await client.getRunByFingerprint("fp");
    await client.getLatestDashboardCapable();
    await client.getRunDashboard(runId);
    await client.getRunHumanReview(runId);
    await client.getRunAde(runId);
    expect(paths).toEqual([
      `/api/v1/intelligence/runs/id/${runId}`,
      "/api/v1/intelligence/runs/fingerprint/fp",
      "/api/v1/intelligence/runs/latest-dashboard-capable",
      `/api/v1/intelligence/runs/id/${runId}/dashboard`,
      `/api/v1/intelligence/runs/id/${runId}/human-review`,
      `/api/v1/intelligence/runs/id/${runId}/ade`,
    ]);
  });
});
