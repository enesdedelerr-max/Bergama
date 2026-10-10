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

  it("keeps HTML, script, and event-handler payloads as inert text nodes", () => {
    const adversarial =
      '<img src=x onerror="window.__hr_pwned=1">' +
      "<script>document.body.setAttribute('data-hr-pwned','1')</script>" +
      '<a href="javascript:alert(1)">click</a>' +
      "<svg onload=\"window.__hr_svg=1\"></svg>";
    const { container } = render(
      <PremarketHumanReviewPanel
        humanReview={baseHr({
          attestation: { recorded_payload: adversarial },
        })}
      />,
    );
    const payloadNode = screen.getByTestId("premarket-hr-payload");
    expect(payloadNode.tagName).toBe("PRE");
    expect(payloadNode).toHaveTextContent(adversarial);
    expect(payloadNode.querySelector("script")).toBeNull();
    expect(payloadNode.querySelector("img")).toBeNull();
    expect(payloadNode.querySelector("a")).toBeNull();
    expect(payloadNode.querySelector("svg")).toBeNull();
    expect(container.querySelector("[data-hr-pwned]")).toBeNull();
    expect(container.innerHTML).not.toContain("dangerouslySetInnerHTML");
    expect(
      (window as unknown as { __hr_pwned?: number }).__hr_pwned,
    ).toBeUndefined();
  });

  it("respects the governed 8192-character boundary without truncating into the UI", () => {
    const exact = "e".repeat(HR_RECORDED_PAYLOAD_MAX_LENGTH);
    const { unmount } = render(
      <PremarketHumanReviewPanel
        humanReview={baseHr({
          attestation: { recorded_payload: exact },
        })}
      />,
    );
    expect(screen.getByTestId("premarket-hr-payload")).toHaveTextContent(exact);
    unmount();

    render(
      <PremarketHumanReviewPanel
        humanReview={baseHr({
          attestation: {
            recorded_payload: `${exact}X`,
          },
        })}
      />,
    );
    expect(
      screen.getByTestId("premarket-hr-payload-oversized"),
    ).toHaveTextContent(String(HR_RECORDED_PAYLOAD_MAX_LENGTH));
    expect(screen.queryByText(`${exact}X`)).not.toBeInTheDocument();
  });
});
