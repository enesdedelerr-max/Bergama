"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { HumanReviewOutput } from "@/contracts/types/product-api";
import {
  HR_RECORDED_PAYLOAD_MAX_LENGTH,
  inspectHrRecordedPayload,
} from "@/lib/premarket/hr-payload";

/**
 * Human Review visibility: known metadata + inert escaped recorded_payload only.
 * Does not render HR records arrays (loosely typed / unknown[]).
 */
export function PremarketHumanReviewPanel({
  humanReview,
}: {
  humanReview: HumanReviewOutput;
}) {
  const inspection = inspectHrRecordedPayload(
    humanReview.attestation?.recorded_payload,
  );

  return (
    <section
      aria-labelledby="premarket-hr-heading"
      data-testid="premarket-human-review-panel"
      className="space-y-3"
    >
      <h2 id="premarket-hr-heading" className="text-base font-semibold">
        Human Review
      </h2>
      <Card>
        <CardHeader>
          <CardTitle>Persisted Human Review metadata</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-2 text-sm sm:grid-cols-2">
            <Meta
              label="human_review_output_id"
              value={humanReview.human_review_output_id}
              mono
            />
            <Meta label="policy_version_id" value={humanReview.policy_version_id} />
            <Meta
              label="ordering_preservation_policy_id"
              value={humanReview.ordering_preservation_policy_id}
            />
            <Meta
              label="presentation_preservation_policy_id"
              value={humanReview.presentation_preservation_policy_id}
            />
            <Meta
              label="human_attestation_policy_id"
              value={humanReview.human_attestation_policy_id}
            />
            <Meta
              label="identity_specification_id"
              value={humanReview.identity_specification_id}
            />
            <Meta
              label="provenance_specification_id"
              value={humanReview.provenance_specification_id}
            />
            <Meta
              label="history_specification_id"
              value={humanReview.history_specification_id}
            />
            <Meta label="as_of" value={humanReview.as_of} />
            <Meta
              label="dashboard_output_id"
              value={humanReview.dashboard_output_id}
              mono
            />
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recorded attestation payload</CardTitle>
        </CardHeader>
        <CardContent>
          {inspection.kind === "valid" ? (
            <pre
              data-testid="premarket-hr-payload"
              className="max-h-96 overflow-auto whitespace-pre-wrap break-all rounded-sm border border-[color:var(--border)] bg-[color:var(--surface)] p-3 font-mono text-xs"
            >
              {inspection.text}
            </pre>
          ) : null}
          {inspection.kind === "empty" ? (
            <p
              data-testid="premarket-hr-payload-empty"
              className="text-sm text-[color:var(--muted-fg)]"
            >
              Recorded payload is empty.
            </p>
          ) : null}
          {inspection.kind === "oversized" ? (
            <p
              role="alert"
              data-testid="premarket-hr-payload-oversized"
              className="text-sm text-[color:var(--muted-fg)]"
            >
              Recorded payload exceeds the authorized maximum of{" "}
              {HR_RECORDED_PAYLOAD_MAX_LENGTH} characters (received{" "}
              {inspection.length}). Excess content is not rendered.
            </p>
          ) : null}
          {inspection.kind === "invalid" ? (
            <p
              role="alert"
              data-testid="premarket-hr-payload-invalid"
              className="text-sm text-[color:var(--muted-fg)]"
            >
              Recorded payload is not a valid string and is not rendered.
            </p>
          ) : null}
        </CardContent>
      </Card>
    </section>
  );
}

function Meta({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div>
      <dt className="text-xs text-[color:var(--muted-fg)]">{label}</dt>
      <dd className={mono ? "break-all font-mono text-xs" : "break-all"}>
        {value}
      </dd>
    </div>
  );
}
