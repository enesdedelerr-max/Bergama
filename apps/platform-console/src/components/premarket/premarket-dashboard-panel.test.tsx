import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PremarketDashboardPanel } from "@/components/premarket/premarket-dashboard-panel";
import type { DashboardPresentationOutput } from "@/contracts/types/product-api";

const dashboard: DashboardPresentationOutput = {
  dashboard_output_id: "a".repeat(64),
  policy_version_id: "dashboard-policy-v1",
  ordering_preservation_policy_id: "ordering-v1",
  presentation_selection_policy_id: "presentation-v1",
  as_of: "2026-10-10T12:00:00Z",
  provenance: { ignored_unknown: true },
  records: [
    {
      sequence_index: 0,
      score_record_id: "b".repeat(64),
      instrument_key: "XNAS.AAPL",
      local_symbol: "AAPL",
      score: "0.42",
      components: {
        watchlist_rank: "0.1",
        gap_magnitude: "0.2",
        catalyst_presence: "0.3",
      },
      watchlist_rank: 1,
      watchlist_rule_id: "rule-1",
      unknown_should_be_skipped: { nested: true },
    },
    "not-an-object",
  ],
};

describe("PremarketDashboardPanel", () => {
  it("renders known dashboard fields and projects known record keys only", () => {
    render(<PremarketDashboardPanel dashboard={dashboard} />);
    expect(screen.getByTestId("premarket-dashboard-panel")).toHaveAttribute(
      "data-ux-state",
      "dashboard_present",
    );
    expect(screen.getByText("dashboard-policy-v1")).toBeInTheDocument();
    expect(screen.getByText("XNAS.AAPL")).toBeInTheDocument();
    expect(screen.getByText("0.42")).toBeInTheDocument();
    expect(screen.getAllByTestId("premarket-dashboard-record")).toHaveLength(1);
    expect(screen.queryByText(/BUY|SELL|LONG|SHORT|safe-to-trade/i)).not.toBeInTheDocument();
    expect(screen.queryByText("unknown_should_be_skipped")).not.toBeInTheDocument();
  });
});
