import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiClientError } from "@/lib/api/errors";
import {
  PremarketAuthExpiredState,
  PremarketAuthLoadingState,
  PremarketBootstrapDisabledState,
  PremarketBootstrapFailedState,
  PremarketInsufficientScopeState,
  PremarketLatestAbsentState,
  PremarketLatestLoadingState,
  PremarketProductFaultState,
  PremarketRefreshingNotice,
  PremarketRunNotFoundState,
  PremarketStageAbsentState,
  PremarketUnauthenticatedState,
} from "@/components/premarket/premarket-states";

afterEach(() => {
  cleanup();
});

describe("Premarket UX state presentations", () => {
  it("renders auth_loading with status semantics", () => {
    render(<PremarketAuthLoadingState />);
    expect(screen.getByRole("status")).toHaveAttribute(
      "data-ux-state",
      "auth_loading",
    );
  });

  it("renders unauthenticated with acquire action", async () => {
    const user = userEvent.setup();
    const onAcquire = vi.fn();
    render(<PremarketUnauthenticatedState onAcquire={onAcquire} />);
    expect(screen.getByRole("alert")).toHaveAttribute(
      "data-ux-state",
      "unauthenticated",
    );
    await user.click(
      screen.getByRole("button", { name: "Acquire bootstrap token" }),
    );
    expect(onAcquire).toHaveBeenCalledTimes(1);
  });

  it("renders auth_expired", () => {
    render(<PremarketAuthExpiredState onAcquire={() => undefined} />);
    expect(screen.getByRole("alert")).toHaveAttribute(
      "data-ux-state",
      "auth_expired",
    );
  });

  it("renders bootstrap_disabled", () => {
    render(<PremarketBootstrapDisabledState />);
    expect(screen.getByRole("alert")).toHaveAttribute(
      "data-ux-state",
      "bootstrap_disabled",
    );
  });

  it("renders bootstrap_failed", () => {
    render(<PremarketBootstrapFailedState onAcquire={() => undefined} />);
    expect(screen.getByRole("alert")).toHaveAttribute(
      "data-ux-state",
      "bootstrap_failed",
    );
  });

  it("renders insufficient_scope", () => {
    render(<PremarketInsufficientScopeState />);
    expect(screen.getByRole("alert")).toHaveAttribute(
      "data-ux-state",
      "insufficient_scope",
    );
  });

  it("renders latest_loading", () => {
    render(<PremarketLatestLoadingState />);
    expect(screen.getByRole("status")).toHaveAttribute(
      "data-ux-state",
      "latest_loading",
    );
  });

  it("renders latest_absent", () => {
    render(<PremarketLatestAbsentState />);
    expect(screen.getByTestId("premarket-latest-absent")).toHaveAttribute(
      "data-ux-state",
      "latest_absent",
    );
  });

  it("renders run_not_found", () => {
    render(<PremarketRunNotFoundState />);
    expect(screen.getByTestId("premarket-run-not-found")).toHaveAttribute(
      "data-ux-state",
      "run_not_found",
    );
  });

  it("renders human_review_absent and ade_absent", () => {
    const { rerender } = render(
      <PremarketStageAbsentState
        state="human_review_absent"
        label="Human Review absent"
      />,
    );
    expect(screen.getByTestId("premarket-human_review_absent")).toHaveAttribute(
      "data-ux-state",
      "human_review_absent",
    );
    rerender(
      <PremarketStageAbsentState state="ade_absent" label="ADE absent" />,
    );
    expect(screen.getByTestId("premarket-ade_absent")).toHaveAttribute(
      "data-ux-state",
      "ade_absent",
    );
  });

  it("renders refreshing", () => {
    render(<PremarketRefreshingNotice />);
    expect(screen.getByRole("status")).toHaveAttribute(
      "data-ux-state",
      "refreshing",
    );
  });

  it("renders product fault states with ProductErrorResponse fields only", () => {
    render(
      <PremarketProductFaultState
        state="corrupt_persisted_snapshot"
        title="Corrupt persisted snapshot"
        error={
          new ApiClientError(
            "intelligence.runs.corrupt_persisted_snapshot",
            "corrupt",
            500,
            "rid-9",
          )
        }
      />,
    );
    expect(
      screen.getByTestId("premarket-corrupt_persisted_snapshot"),
    ).toHaveAttribute("data-ux-state", "corrupt_persisted_snapshot");
    expect(
      screen.getByText("intelligence.runs.corrupt_persisted_snapshot"),
    ).toBeInTheDocument();
    expect(screen.getByText("rid-9")).toBeInTheDocument();
    expect(
      screen.queryByText(/BUY|SELL|safe-to-trade|live/i),
    ).not.toBeInTheDocument();
  });
});
