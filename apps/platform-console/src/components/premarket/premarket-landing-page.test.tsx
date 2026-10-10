import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PremarketLandingPage } from "@/components/premarket/premarket-landing-page";
import { ApiClientError } from "@/lib/api/errors";

const authState = vi.hoisted(() => ({
  value: "AUTHENTICATED" as string,
}));

const getLatestDashboardCapable = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("@/lib/auth/auth-token-provider", () => ({
  useAuthToken: () => ({
    state: authState.value,
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
    getLatestDashboardCapable,
    getRunByFingerprint: vi.fn(),
  }),
}));

function renderLanding() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return render(<PremarketLandingPage />, { wrapper });
}

afterEach(() => {
  cleanup();
});

describe("PremarketLandingPage", () => {
  beforeEach(() => {
    authState.value = "AUTHENTICATED";
    getLatestDashboardCapable.mockReset();
  });

  it("renders unauthenticated auth UX without product queries", () => {
    authState.value = "UNAUTHENTICATED";
    renderLanding();
    expect(screen.getByRole("heading", { name: "Premarket" })).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveAttribute(
      "data-ux-state",
      "unauthenticated",
    );
    expect(getLatestDashboardCapable).not.toHaveBeenCalled();
  });

  it("loads latest dashboard-capable success with freshness fields", async () => {
    getLatestDashboardCapable.mockResolvedValue({
      run_id: "run-latest",
      as_of: "2026-10-10T12:00:00Z",
      persisted_at: "2026-10-10T12:05:00Z",
      age_seconds: 120,
      outcome: "completed",
      snapshot_contract_version: "v1",
      persistence_schema_version: "v1",
      stage_presence: {},
      provenance: {},
    });
    renderLanding();
    expect(
      await screen.findByTestId("premarket-latest-success"),
    ).toBeInTheDocument();
    expect(screen.getByText("run-latest")).toBeInTheDocument();
    expect(screen.getByText("120")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open run detail" })).toHaveAttribute(
      "href",
      "/premarket/runs/run-latest",
    );
    expect(screen.queryByText(/live|safe-to-trade/i)).not.toBeInTheDocument();
  });

  it("maps latest absent and storage unavailable", async () => {
    getLatestDashboardCapable.mockRejectedValue(
      new ApiClientError("not.found", "missing", 404, "r1"),
    );
    const { unmount } = renderLanding();
    expect(await screen.findByTestId("premarket-latest-absent")).toBeInTheDocument();
    unmount();

    getLatestDashboardCapable.mockRejectedValue(
      new ApiClientError(
        "intelligence.runs.storage_unavailable",
        "down",
        503,
        "r2",
      ),
    );
    renderLanding();
    await waitFor(() => {
      expect(
        screen.getByTestId("premarket-storage_unavailable"),
      ).toBeInTheDocument();
    });
  });
});
