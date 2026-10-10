"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DashboardPresentationOutput } from "@/contracts/types/product-api";
import { projectDashboardRecords } from "@/lib/premarket/dashboard-fields";

export function PremarketDashboardPanel({
  dashboard,
}: {
  dashboard: DashboardPresentationOutput;
}) {
  const records = projectDashboardRecords(dashboard.records);

  return (
    <section
      aria-labelledby="premarket-dashboard-heading"
      data-ux-state="dashboard_present"
      data-testid="premarket-dashboard-panel"
      className="space-y-3"
    >
      <h2 id="premarket-dashboard-heading" className="text-base font-semibold">
        Dashboard snapshot
      </h2>
      <Card>
        <CardHeader>
          <CardTitle>Persisted dashboard fields</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-2 text-sm sm:grid-cols-2">
            <Field label="dashboard_output_id" value={dashboard.dashboard_output_id} mono />
            <Field label="policy_version_id" value={dashboard.policy_version_id} />
            <Field
              label="ordering_preservation_policy_id"
              value={dashboard.ordering_preservation_policy_id}
            />
            <Field
              label="presentation_selection_policy_id"
              value={dashboard.presentation_selection_policy_id}
            />
            <Field label="as_of" value={dashboard.as_of} />
          </dl>
        </CardContent>
      </Card>

      {records.length === 0 ? (
        <p className="text-sm text-[color:var(--muted-fg)]">
          No projectable dashboard records in this snapshot.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[40rem] border-collapse text-left text-sm">
            <caption className="sr-only">
              Known dashboard presentation records
            </caption>
            <thead>
              <tr className="border-b border-[color:var(--border)] text-xs uppercase tracking-wide text-[color:var(--muted-fg)]">
                <th scope="col" className="px-2 py-2 font-medium">
                  seq
                </th>
                <th scope="col" className="px-2 py-2 font-medium">
                  instrument
                </th>
                <th scope="col" className="px-2 py-2 font-medium">
                  score
                </th>
                <th scope="col" className="px-2 py-2 font-medium">
                  watchlist_rank
                </th>
                <th scope="col" className="px-2 py-2 font-medium">
                  components
                </th>
              </tr>
            </thead>
            <tbody>
              {records.map((record, index) => (
                <tr
                  key={record.score_record_id ?? `row-${index}`}
                  className="border-b border-[color:var(--border)]"
                  data-testid="premarket-dashboard-record"
                >
                  <td className="px-2 py-2 font-mono text-xs">
                    {record.sequence_index ?? "—"}
                  </td>
                  <td className="px-2 py-2">
                    <div>{record.instrument_key ?? "—"}</div>
                    {record.local_symbol ? (
                      <div className="text-xs text-[color:var(--muted-fg)]">
                        {record.local_symbol}
                      </div>
                    ) : null}
                  </td>
                  <td className="px-2 py-2 font-mono text-xs">
                    {record.score ?? "—"}
                  </td>
                  <td className="px-2 py-2 font-mono text-xs">
                    {record.watchlist_rank ?? "—"}
                  </td>
                  <td className="px-2 py-2 font-mono text-xs">
                    {record.components
                      ? [
                          `wr=${record.components.watchlist_rank ?? "—"}`,
                          `gap=${record.components.gap_magnitude ?? "—"}`,
                          `cat=${record.components.catalyst_presence ?? "—"}`,
                        ].join(" ")
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
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
