import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PremarketAdePanel } from "@/components/premarket/premarket-ade-panel";
import type { AdeProductSnapshotRead } from "@/contracts/types/product-api";

const ade: AdeProductSnapshotRead = {
  outcome_kind: "accepted",
  policy_version_id: "ade-policy",
  as_of: "2026-10-10T12:00:00Z",
  reason_family: "policy",
  decision_id: "decision-1",
  human_review_output_id: "hr-1",
  detail: "recorded detail",
  provenance: {
    policy_version_id: "ade-policy",
    identity_specification_id: "id-spec",
    provenance_specification_id: "prov-spec",
    acceptance_specification_id: "acc-spec",
    digest_method_id: "digest",
    derivation_attribution_id: "deriv",
    as_of: "2026-10-10T12:00:00Z",
    recorded_attestation_fingerprint: "fp".padEnd(64, "0"),
    config_fingerprint: "cf".padEnd(64, "1"),
    evidence_fingerprint: "ef".padEnd(64, "2"),
  },
};

describe("PremarketAdePanel", () => {
  it("renders public ADE fields and excludes private payload / CTAs", () => {
    render(<PremarketAdePanel ade={ade} />);
    expect(screen.getByTestId("premarket-ade-panel")).toBeInTheDocument();
    expect(screen.getByText("accepted")).toBeInTheDocument();
    expect(screen.getByText("recorded detail")).toBeInTheDocument();
    expect(
      screen.getByText("fp".padEnd(64, "0")),
    ).toBeInTheDocument();
    expect(screen.queryByText(/recorded_attestation_payload/i)).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: /invoke|model|trade|execute|recommend/i,
      }),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/BUY|SELL|safe-to-trade/i)).not.toBeInTheDocument();
  });
});
