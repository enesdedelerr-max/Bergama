import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PremarketLandingPage } from "@/components/premarket/premarket-landing-page";
import { PremarketLookupControls } from "@/components/premarket/premarket-lookup-controls";
import {
  PremarketAuthLoadingState,
  PremarketFailClosedError,
  PremarketLatestLoadingState,
  PremarketProductFaultState,
  PremarketUnauthenticatedState,
} from "@/components/premarket/premarket-states";
import { ApiClientError } from "@/lib/api/errors";

const authState = vi.hoisted(() => ({
  value: "UNAUTHENTICATED" as string,
}));

const getLatestDashboardCapable = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("@/lib/auth/auth-token-provider", () => ({
  useAuthToken: () => ({
    state: authState.value,
    getAccessToken: () => (authState.value === "AUTHENTICATED" ? "token" : null),
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

function renderWithQuery(ui: ReactNode) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(ui, {
    wrapper: ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    ),
  });
}

afterEach(() => {
  cleanup();
});

describe("Premarket accessibility baseline", () => {
  beforeEach(() => {
    authState.value = "UNAUTHENTICATED";
    getLatestDashboardCapable.mockReset();
  });

  it("exposes semantic headings and labeled lookup controls", () => {
    renderWithQuery(<PremarketLandingPage />);
    expect(
      screen.getByRole("heading", { level: 1, name: "Premarket" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Lookup persisted run" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Run ID")).toBeInTheDocument();
    expect(screen.getByLabelText(/Fingerprint/)).toBeInTheDocument();
  });

  it("announces loading and auth states with status semantics and accessible names", () => {
    const { unmount } = render(<PremarketAuthLoadingState />);
    const authLoading = screen.getByRole("status", {
      name: "Authenticating product access",
    });
    expect(authLoading).toHaveAttribute("data-ux-state", "auth_loading");
    expect(authLoading).toHaveAttribute("aria-live", "polite");
    unmount();

    render(<PremarketLatestLoadingState />);
    const latestLoading = screen.getByRole("status", {
      name: "Loading latest dashboard-capable run",
    });
    expect(latestLoading).toHaveAttribute("data-ux-state", "latest_loading");
    expect(latestLoading).toHaveAttribute("aria-live", "polite");
  });

  it("presents fail-closed errors as alerts with textual meaning (not color-only)", () => {
    const { unmount } = render(
      <PremarketProductFaultState
        state="storage_unavailable"
        title="Storage unavailable"
        error={
          new ApiClientError(
            "intelligence.runs.storage_unavailable",
            "storage unavailable",
            503,
            "req-a11y",
          )
        }
      />,
    );
    const storageAlert = screen.getByRole("alert");
    expect(storageAlert).toHaveAttribute("data-ux-state", "storage_unavailable");
    expect(storageAlert).toHaveTextContent("Storage unavailable");
    expect(storageAlert).toHaveTextContent("storage unavailable");
    unmount();

    render(
      <PremarketFailClosedError
        error={
          new ApiClientError(
            "product_error.unknown",
            "Unknown product failure",
            500,
            "req-fail",
          )
        }
      />,
    );
    const failClosed = screen.getByTestId("premarket-fail-closed");
    expect(failClosed).toHaveAttribute("role", "alert");
    expect(failClosed).toHaveTextContent("Product error");
    expect(failClosed).toHaveTextContent("Unknown product failure");
  });

  it("keeps bootstrap acquire control keyboard-reachable", async () => {
    const user = userEvent.setup();
    const onAcquire = vi.fn();
    render(<PremarketUnauthenticatedState onAcquire={onAcquire} />);
    const button = screen.getByRole("button", {
      name: "Acquire bootstrap token",
    });
    button.focus();
    expect(button).toHaveFocus();
    await user.keyboard("{Enter}");
    expect(onAcquire).toHaveBeenCalledTimes(1);
  });

  it("keeps run-ID lookup keyboard operable via labeled control", async () => {
    const user = userEvent.setup();
    render(<PremarketLookupControls enabled />);
    const runId = screen.getByLabelText("Run ID");
    await user.type(runId, "run-a11y");
    expect(runId).toHaveValue("run-a11y");
    const open = screen.getByRole("button", { name: "Open run" });
    open.focus();
    expect(open).toHaveFocus();
  });

  it("surfaces unauthenticated product gate with alert text, not color alone", () => {
    renderWithQuery(<PremarketLandingPage />);
    const alert = screen.getByRole("alert");
    expect(alert).toHaveAttribute("data-ux-state", "unauthenticated");
    expect(alert).toHaveTextContent(/Product authentication required/i);
    expect(alert).toHaveTextContent(/intelligence:runs:read/i);
  });
});
