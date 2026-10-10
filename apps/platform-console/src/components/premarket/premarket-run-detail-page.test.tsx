import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PremarketRunDetailPage } from "@/components/premarket/premarket-run-detail-page";
import { ApiClientError } from "@/lib/api/errors";

const getRunById = vi.fn();
const getRunDashboard = vi.fn();
const getRunHumanReview = vi.fn();
const getRunAde = vi.fn();

vi.mock("@/lib/auth/auth-token-provider", () => ({
  useAuthToken: () => ({
    state: "AUTHENTICATED",
    getAccessToken: () => "token",
    getAuthGeneration: () => 1,
    reacquireOnce: async () => false,
    markInsufficientScope: () => undefined,
    acquireBootstrap: async () => true,
    logout: () => undefined,
    scopes: ["intelligence:runs:read"],
    authStates: [],
  }),
}));

vi.mock("@/lib/api/intelligence-client", () => ({
  createIntelligenceClient: () => ({
    getRunById,
    getRunDashboard,
    getRunHumanReview,
    getRunAde,
  }),
}));

function renderDetail(runId = "run-1") {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return render(<PremarketRunDetailPage runId={runId} />, { wrapper });
}

afterEach(() => {
  cleanup();
});

describe("PremarketRunDetailPage", () => {
  beforeEach(() => {
    getRunById.mockReset();
    getRunDashboard.mockReset();
    getRunHumanReview.mockReset();
    getRunAde.mockReset();
  });

  it("renders run metadata, dashboard, and stage absence for HR/ADE", async () => {
    getRunById.mockResolvedValue({
      run_id: "run-1",
      pipeline_fingerprint: "ab".repeat(32),
      as_of: "2026-10-10T12:00:00Z",
      persisted_at: "2026-10-10T12:05:00Z",
      age_seconds: 30,
      snapshot_contract_version: "v1",
      persistence_schema_version: "v1",
      outcome: "completed",
      stage_presence: { dashboard: "present", human_review: "absent", ade: "absent" },
      provenance: {},
    });
    getRunDashboard.mockResolvedValue({
      run_id: "run-1",
      dashboard: {
        dashboard_output_id: "d".repeat(64),
        policy_version_id: "dash-pol",
        ordering_preservation_policy_id: "ord",
        presentation_selection_policy_id: "pres",
        as_of: "2026-10-10T12:00:00Z",
        records: [],
        provenance: {},
      },
    });
    getRunHumanReview.mockRejectedValue(
      new ApiClientError(
        "intelligence.runs.stage_not_present",
        "absent",
        404,
        null,
      ),
    );
    getRunAde.mockRejectedValue(
      new ApiClientError(
        "intelligence.runs.stage_not_present",
        "absent",
        404,
        null,
      ),
    );

    renderDetail();
    expect(await screen.findByTestId("premarket-run-metadata")).toBeInTheDocument();
    expect(screen.getByText("30")).toBeInTheDocument();
    expect(await screen.findByTestId("premarket-dashboard-panel")).toBeInTheDocument();
    expect(
      await screen.findByTestId("premarket-human_review_absent"),
    ).toBeInTheDocument();
    expect(await screen.findByTestId("premarket-ade_absent")).toBeInTheDocument();
    expect(screen.queryByText(/BUY|SELL|invoke|broker/i)).not.toBeInTheDocument();
  });

  it("maps run_not_found without inventing data", async () => {
    getRunById.mockRejectedValue(
      new ApiClientError(
        "intelligence.runs.run_not_found",
        "missing",
        404,
        "req",
      ),
    );
    renderDetail("missing-run");
    await waitFor(() => {
      expect(screen.getByTestId("premarket-run-not-found")).toBeInTheDocument();
    });
    expect(getRunDashboard).not.toHaveBeenCalled();
  });
});
