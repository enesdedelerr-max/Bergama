import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PremarketLookupControls } from "@/components/premarket/premarket-lookup-controls";

const push = vi.fn();
const getRunByFingerprint = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

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
    getRunByFingerprint,
  }),
}));

afterEach(() => {
  cleanup();
});

describe("PremarketLookupControls", () => {
  beforeEach(() => {
    push.mockReset();
    getRunByFingerprint.mockReset();
  });

  it("navigates on run-ID submit and ignores empty input", async () => {
    const user = userEvent.setup();
    render(<PremarketLookupControls enabled />);
    await user.click(screen.getByRole("button", { name: "Open run" }));
    expect(push).not.toHaveBeenCalled();
    await user.type(screen.getByLabelText("Run ID"), "  run-abc  ");
    await user.click(screen.getByRole("button", { name: "Open run" }));
    expect(push).toHaveBeenCalledWith("/premarket/runs/run-abc");
  });

  it("validates fingerprint locally and navigates after successful lookup", async () => {
    const user = userEvent.setup();
    const fingerprint = "ab".repeat(32);
    getRunByFingerprint.mockResolvedValue({ run_id: "run-from-fp" });
    render(<PremarketLookupControls enabled />);

    const fingerprintInput = screen.getByLabelText(/Fingerprint/);
    await user.type(fingerprintInput, "not-hex");
    await user.click(
      screen.getByRole("button", { name: "Lookup fingerprint" }),
    );
    expect(
      screen.getByTestId("premarket-fingerprint-invalid"),
    ).toBeInTheDocument();
    expect(getRunByFingerprint).not.toHaveBeenCalled();

    await user.clear(fingerprintInput);
    await user.type(fingerprintInput, fingerprint.toUpperCase());
    await user.click(
      screen.getByRole("button", { name: "Lookup fingerprint" }),
    );
    await waitFor(() => {
      expect(getRunByFingerprint).toHaveBeenCalledWith(fingerprint);
      expect(push).toHaveBeenCalledWith("/premarket/runs/run-from-fp");
    });
  });
});
