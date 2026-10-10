import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { PremarketHumanReviewPanel } from "@/components/premarket/premarket-human-review-panel";
import type { HumanReviewOutput } from "@/contracts/types/product-api";
import { HR_RECORDED_PAYLOAD_MAX_LENGTH } from "@/lib/premarket/hr-payload";

afterEach(() => {
  cleanup();
});

function baseHr(overrides: Partial<HumanReviewOutput> = {}): HumanReviewOutput {
  return {
    human_review_output_id: "hr-1",
    policy_version_id: "hr-policy",
    ordering_preservation_policy_id: "ord",
    presentation_preservation_policy_id: "pres",
    human_attestation_policy_id: "att",
    identity_specification_id: "id",
    provenance_specification_id: "prov",
    history_specification_id: "hist",
    as_of: "2026-10-10T12:00:00Z",
    dashboard_output_id: "c".repeat(64),
    records: [{ should_not_render: true }],
    attestation: { recorded_payload: "safe <script>payload</script>" },
    provenance: { nested: true },
    history: { nested: true },
    ...overrides,
  };
}

describe("PremarketHumanReviewPanel", () => {
  it("renders inert escaped recorded_payload text and known metadata only", () => {
    const { container } = render(
      <PremarketHumanReviewPanel humanReview={baseHr()} />,
    );
    expect(screen.getByTestId("premarket-hr-payload")).toHaveTextContent(
      "safe <script>payload</script>",
    );
    expect(container.innerHTML).not.toContain("dangerouslySetInnerHTML");
    expect(screen.queryByText("should_not_render")).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /approve|reject|submit/i }),
    ).not.toBeInTheDocument();
  });

  it("does not render oversized payload content", () => {
    render(
      <PremarketHumanReviewPanel
        humanReview={baseHr({
          attestation: {
            recorded_payload: "z".repeat(HR_RECORDED_PAYLOAD_MAX_LENGTH + 5),
          },
        })}
      />,
    );
    expect(
      screen.getByTestId("premarket-hr-payload-oversized"),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("premarket-hr-payload")).not.toBeInTheDocument();
  });
});
