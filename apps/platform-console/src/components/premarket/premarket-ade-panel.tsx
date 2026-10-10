"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type {
  AdeProductProvenanceRead,
  AdeProductSnapshotRead,
} from "@/contracts/types/product-api";

/**
 * ADE visibility-only presentation of public DTO fields.
 * Never renders recorded_attestation_payload or unknown keys.
 */
export function PremarketAdePanel({ ade }: { ade: AdeProductSnapshotRead }) {
  return (
    <section
      aria-labelledby="premarket-ade-heading"
      data-testid="premarket-ade-panel"
      className="space-y-3"
    >
      <h2 id="premarket-ade-heading" className="text-base font-semibold">
        ADE snapshot
      </h2>
      <Card>
        <CardHeader>
          <CardTitle>Public ADE fields</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-2 text-sm sm:grid-cols-2">
            <Field label="outcome_kind" value={ade.outcome_kind} />
            <Field label="policy_version_id" value={ade.policy_version_id} />
            <Field label="as_of" value={ade.as_of} />
            <Field label="reason_family" value={ade.reason_family} />
            <Field label="decision_id" value={ade.decision_id ?? "—"} mono />
            <Field
              label="human_review_output_id"
              value={ade.human_review_output_id ?? "—"}
              mono
            />
            <Field label="detail" value={ade.detail ?? "—"} />
          </dl>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Public ADE provenance</CardTitle>
        </CardHeader>
        <CardContent>
          <AdeProvenanceFields provenance={ade.provenance} />
        </CardContent>
      </Card>
    </section>
  );
}

function AdeProvenanceFields({
  provenance,
}: {
  provenance: AdeProductProvenanceRead;
}) {
  const entries: Array<[string, string]> = [
    ["policy_version_id", provenance.policy_version_id],
    ["identity_specification_id", provenance.identity_specification_id],
    ["provenance_specification_id", provenance.provenance_specification_id],
    ["acceptance_specification_id", provenance.acceptance_specification_id],
    ["digest_method_id", provenance.digest_method_id],
    ["derivation_attribution_id", provenance.derivation_attribution_id],
    ["as_of", provenance.as_of],
    [
      "human_review_output_id",
      provenance.human_review_output_id ?? "—",
    ],
    [
      "human_review_policy_version_id",
      provenance.human_review_policy_version_id ?? "—",
    ],
    [
      "human_review_identity_specification_id",
      provenance.human_review_identity_specification_id ?? "—",
    ],
    [
      "human_review_provenance_specification_id",
      provenance.human_review_provenance_specification_id ?? "—",
    ],
    [
      "human_review_config_fingerprint",
      provenance.human_review_config_fingerprint ?? "—",
    ],
    [
      "human_review_input_fingerprint",
      provenance.human_review_input_fingerprint ?? "—",
    ],
    [
      "recorded_attestation_fingerprint",
      provenance.recorded_attestation_fingerprint ?? "—",
    ],
    ["config_fingerprint", provenance.config_fingerprint],
    ["evidence_fingerprint", provenance.evidence_fingerprint],
  ];

  return (
    <dl className="grid gap-2 text-sm sm:grid-cols-2">
      {entries.map(([label, value]) => (
        <Field key={label} label={label} value={value} mono={label.includes("fingerprint") || label.endsWith("_id")} />
      ))}
    </dl>
  );
}

function Field({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div data-ade-field={label}>
      <dt className="text-xs text-[color:var(--muted-fg)]">{label}</dt>
      <dd className={mono ? "break-all font-mono text-xs" : "break-all"}>
        {value}
      </dd>
    </div>
  );
}
