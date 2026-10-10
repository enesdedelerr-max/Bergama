"use client";

import type { ReactNode } from "react";
import { PremarketAdePanel } from "@/components/premarket/premarket-ade-panel";
import { PremarketDashboardPanel } from "@/components/premarket/premarket-dashboard-panel";
import { PremarketHumanReviewPanel } from "@/components/premarket/premarket-human-review-panel";
import { PremarketRunMetadata } from "@/components/premarket/premarket-run-metadata";
import {
  PremarketAuthExpiredState,
  PremarketAuthLoadingState,
  PremarketBootstrapDisabledState,
  PremarketBootstrapFailedState,
  PremarketFailClosedError,
  PremarketInsufficientScopeState,
  PremarketLatestLoadingState,
  PremarketProductFaultState,
  PremarketRefreshingNotice,
  PremarketRunNotFoundState,
  PremarketStageAbsentState,
  PremarketUnauthenticatedState,
} from "@/components/premarket/premarket-states";
import {
  useIntelligenceRunById,
  useRunAde,
  useRunDashboard,
  useRunHumanReview,
} from "@/hooks/use-premarket-queries";
import { useAuthToken } from "@/lib/auth/auth-token-provider";
import { mapProductErrorToUxState } from "@/lib/premarket/map-product-error";

export function PremarketRunDetailPage({ runId }: { runId: string }) {
  const auth = useAuthToken();
  const authenticated = auth.state === "AUTHENTICATED";
  const runQuery = useIntelligenceRunById(runId, authenticated);
  const runReady = authenticated && runQuery.isSuccess;
  const dashboardQuery = useRunDashboard(runId, runReady);
  const humanReviewQuery = useRunHumanReview(runId, runReady);
  const adeQuery = useRunAde(runId, runReady);

  return (
    <div className="space-y-6" data-testid="premarket-run-detail">
      <header className="space-y-1">
        <h1 className="text-xl font-semibold tracking-tight">Premarket run</h1>
        <p className="break-all font-mono text-xs text-[color:var(--muted-fg)]">
          {runId}
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
          {runQuery.isPending ? <PremarketLatestLoadingState /> : null}
          {runQuery.isError ? (
            <RunIdentityError error={runQuery.error} />
          ) : null}
          {runQuery.data ? (
            <>
              <div className="flex justify-end">
                {runQuery.isFetching ||
                dashboardQuery.isFetching ||
                humanReviewQuery.isFetching ||
                adeQuery.isFetching ? (
                  <PremarketRefreshingNotice />
                ) : null}
              </div>
              <PremarketRunMetadata run={runQuery.data} />
              <StageSection
                query={dashboardQuery}
                endpoint="dashboard"
                renderSuccess={(payload) => (
                  <PremarketDashboardPanel dashboard={payload.dashboard} />
                )}
              />
              <StageSection
                query={humanReviewQuery}
                endpoint="human_review"
                absentState="human_review_absent"
                absentLabel="Human Review absent"
                renderSuccess={(payload) => (
                  <PremarketHumanReviewPanel
                    humanReview={payload.human_review}
                  />
                )}
              />
              <StageSection
                query={adeQuery}
                endpoint="ade"
                absentState="ade_absent"
                absentLabel="ADE absent"
                renderSuccess={(payload) => (
                  <PremarketAdePanel ade={payload.ade} />
                )}
              />
            </>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

function RunIdentityError({ error }: { error: unknown }) {
  const ux = mapProductErrorToUxState(error, "run");
  if (ux === "run_not_found") {
    return <PremarketRunNotFoundState />;
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

function StageSection<T>({
  query,
  endpoint,
  absentState,
  absentLabel,
  renderSuccess,
}: {
  query: {
    isPending: boolean;
    isError: boolean;
    error: unknown;
    data: T | undefined;
  };
  endpoint: "dashboard" | "human_review" | "ade";
  absentState?: "human_review_absent" | "ade_absent";
  absentLabel?: string;
  renderSuccess: (data: T) => ReactNode;
}) {
  if (query.isPending) {
    return <PremarketLatestLoadingState />;
  }
  if (query.isError) {
    const ux = mapProductErrorToUxState(query.error, endpoint);
    if (
      (ux === "human_review_absent" || ux === "ade_absent") &&
      absentState &&
      absentLabel
    ) {
      return (
        <PremarketStageAbsentState state={absentState} label={absentLabel} />
      );
    }
    if (ux === "run_not_found") {
      return <PremarketRunNotFoundState />;
    }
    if (ux === "insufficient_scope") {
      return <PremarketInsufficientScopeState />;
    }
    if (ux === "unsupported_snapshot_contract") {
      return (
        <PremarketProductFaultState
          state="unsupported_snapshot_contract"
          title="Unsupported snapshot contract"
          error={query.error}
        />
      );
    }
    if (ux === "corrupt_persisted_snapshot") {
      return (
        <PremarketProductFaultState
          state="corrupt_persisted_snapshot"
          title="Corrupt persisted snapshot"
          error={query.error}
        />
      );
    }
    if (ux === "storage_unavailable") {
      return (
        <PremarketProductFaultState
          state="storage_unavailable"
          title="Storage unavailable"
          error={query.error}
        />
      );
    }
    if (ux === "network_unavailable") {
      return (
        <PremarketProductFaultState
          state="network_unavailable"
          title="Network unavailable"
          error={query.error}
        />
      );
    }
    return <PremarketFailClosedError error={query.error} />;
  }
  if (!query.data) {
    return null;
  }
  return <>{renderSuccess(query.data)}</>;
}
