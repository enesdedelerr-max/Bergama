"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PremarketLookupControls } from "@/components/premarket/premarket-lookup-controls";
import {
  PremarketAuthExpiredState,
  PremarketAuthLoadingState,
  PremarketBootstrapDisabledState,
  PremarketBootstrapFailedState,
  PremarketFailClosedError,
  PremarketInsufficientScopeState,
  PremarketLatestAbsentState,
  PremarketLatestLoadingState,
  PremarketProductFaultState,
  PremarketRefreshingNotice,
  PremarketUnauthenticatedState,
} from "@/components/premarket/premarket-states";
import { useLatestDashboardCapable } from "@/hooks/use-premarket-queries";
import { useAuthToken } from "@/lib/auth/auth-token-provider";
import { mapProductErrorToUxState } from "@/lib/premarket/map-product-error";

export function PremarketLandingPage() {
  const auth = useAuthToken();
  const authenticated = auth.state === "AUTHENTICATED";
  const latest = useLatestDashboardCapable(authenticated);

  return (
    <div className="space-y-6" data-testid="premarket-landing">
      <header className="space-y-1">
        <h1 className="text-xl font-semibold tracking-tight">Premarket</h1>
        <p className="text-sm text-[color:var(--muted-fg)]">
          Read-only view of persisted intelligence runs. No recomputation,
          trading actions, or model participation.
        </p>
      </header>

      {auth.state === "BOOTSTRAP_LOADING" ? <PremarketAuthLoadingState /> : null}
      {auth.state === "UNAUTHENTICATED" ? (
        <PremarketUnauthenticatedState
          onAcquire={() => {
            void auth.acquireBootstrap();
          }}
        />
      ) : null}
      {auth.state === "EXPIRED" ? (
        <PremarketAuthExpiredState
          onAcquire={() => {
            void auth.acquireBootstrap();
          }}
        />
      ) : null}
      {auth.state === "BOOTSTRAP_DISABLED" ? (
        <PremarketBootstrapDisabledState />
      ) : null}
      {auth.state === "BOOTSTRAP_FAILED" ? (
        <PremarketBootstrapFailedState
          onAcquire={() => {
            void auth.acquireBootstrap();
          }}
        />
      ) : null}
      {auth.state === "INSUFFICIENT_SCOPE" ? (
        <PremarketInsufficientScopeState />
      ) : null}

      {authenticated ? (
        <>
          <LatestDashboardCapableSection
            isPending={latest.isPending}
            isFetching={latest.isFetching}
            isError={latest.isError}
            error={latest.error}
            data={latest.data}
          />
          <PremarketLookupControls enabled />
        </>
      ) : (
        <PremarketLookupControls enabled={false} />
      )}
    </div>
  );
}

function LatestDashboardCapableSection({
  isPending,
  isFetching,
  isError,
  error,
  data,
}: {
  isPending: boolean;
  isFetching: boolean;
  isError: boolean;
  error: unknown;
  data:
    | {
        run_id: string;
        as_of?: string | null;
        persisted_at: string;
        age_seconds: number;
        outcome: string;
        snapshot_contract_version: string;
      }
    | undefined;
}) {
  if (isPending) {
    return <PremarketLatestLoadingState />;
  }

  if (isError) {
    const ux = mapProductErrorToUxState(error, "latest");
    if (ux === "latest_absent") {
      return <PremarketLatestAbsentState />;
    }
    if (ux === "run_not_found") {
      return <PremarketLatestAbsentState />;
    }
    if (ux === "insufficient_scope") {
      return <PremarketInsufficientScopeState />;
    }
    if (ux === "unsupported_snapshot_contract") {
      return (
        <PremarketProductFaultState
          state="unsupported_snapshot_contract"
          title="Unsupported snapshot contract"
          error={error}
        />
      );
    }
    if (ux === "corrupt_persisted_snapshot") {
      return (
        <PremarketProductFaultState
          state="corrupt_persisted_snapshot"
          title="Corrupt persisted snapshot"
          error={error}
        />
      );
    }
    if (ux === "storage_unavailable") {
      return (
        <PremarketProductFaultState
          state="storage_unavailable"
          title="Storage unavailable"
          error={error}
        />
      );
    }
    if (ux === "network_unavailable") {
      return (
        <PremarketProductFaultState
          state="network_unavailable"
          title="Network unavailable"
          error={error}
        />
      );
    }
    return <PremarketFailClosedError error={error} />;
  }

  if (!data) {
    return <PremarketLatestAbsentState />;
  }

  return (
    <section
      aria-labelledby="premarket-latest-heading"
      data-ux-state="success"
      data-testid="premarket-latest-success"
      className="space-y-2"
    >
      <div className="flex items-center justify-between gap-3">
        <h2 id="premarket-latest-heading" className="text-base font-semibold">
          Latest dashboard-capable run
        </h2>
        {isFetching ? <PremarketRefreshingNotice /> : null}
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="font-mono text-xs">{data.run_id}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <dl className="grid gap-2 sm:grid-cols-2">
            <div>
              <dt className="text-xs text-[color:var(--muted-fg)]">as_of</dt>
              <dd>{data.as_of ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-xs text-[color:var(--muted-fg)]">
                persisted_at
              </dt>
              <dd>{data.persisted_at}</dd>
            </div>
            <div>
              <dt className="text-xs text-[color:var(--muted-fg)]">
                age_seconds
              </dt>
              <dd>{data.age_seconds}</dd>
            </div>
            <div>
              <dt className="text-xs text-[color:var(--muted-fg)]">outcome</dt>
              <dd>{data.outcome}</dd>
            </div>
            <div>
              <dt className="text-xs text-[color:var(--muted-fg)]">
                snapshot_contract_version
              </dt>
              <dd>{data.snapshot_contract_version}</dd>
            </div>
          </dl>
          <Link
            href={`/premarket/runs/${encodeURIComponent(data.run_id)}`}
            className="inline-flex text-sm font-medium text-[color:var(--accent)] underline-offset-4 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
          >
            Open run detail
          </Link>
        </CardContent>
      </Card>
    </section>
  );
}
