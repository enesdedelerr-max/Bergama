"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { IntelligenceRunRead } from "@/contracts/types/product-api";

export function PremarketRunMetadata({ run }: { run: IntelligenceRunRead }) {
  const stageEntries = Object.entries(run.stage_presence ?? {});

  return (
    <section
      aria-labelledby="premarket-run-meta-heading"
      data-testid="premarket-run-metadata"
      data-ux-state="success"
      className="space-y-3"
    >
      <h2 id="premarket-run-meta-heading" className="text-base font-semibold">
        Run identity and freshness
      </h2>
      <Card>
        <CardHeader>
          <CardTitle>Persisted run metadata</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-2 text-sm sm:grid-cols-2">
            <Field label="run_id" value={run.run_id} mono />
            <Field
              label="pipeline_fingerprint"
              value={run.pipeline_fingerprint ?? "—"}
              mono
            />
            <Field label="as_of" value={run.as_of ?? "—"} />
            <Field label="persisted_at" value={run.persisted_at} />
            <Field label="age_seconds" value={String(run.age_seconds)} />
            <Field
              label="snapshot_contract_version"
              value={run.snapshot_contract_version}
            />
            <Field
              label="persistence_schema_version"
              value={run.persistence_schema_version}
            />
            <Field label="outcome" value={run.outcome} />
            <Field label="failed_stage" value={run.failed_stage ?? "—"} />
            <Field
              label="failure_error_type"
              value={run.failure_error_type ?? "—"}
            />
            <Field label="failure_detail" value={run.failure_detail ?? "—"} />
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Stage presence</CardTitle>
        </CardHeader>
        <CardContent>
          {stageEntries.length === 0 ? (
            <p className="text-sm text-[color:var(--muted-fg)]">
              No stage presence entries reported.
            </p>
          ) : (
            <ul className="grid gap-1 text-sm sm:grid-cols-2">
              {stageEntries.map(([stage, presence]) => (
                <li key={stage} className="font-mono text-xs">
                  {stage}: {presence}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </section>
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
    <div>
      <dt className="text-xs text-[color:var(--muted-fg)]">{label}</dt>
      <dd className={mono ? "break-all font-mono text-xs" : "break-all"}>
        {value}
      </dd>
    </div>
  );
}
