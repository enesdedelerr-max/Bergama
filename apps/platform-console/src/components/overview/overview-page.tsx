"use client";

import { useSearchParams } from "next/navigation";
import { ServiceStatusCard } from "@/components/overview/service-status-card";
import { ServiceStatusTable } from "@/components/overview/service-status-table";
import {
  OverviewEmptyState,
  OverviewErrorState,
  OverviewLoadingState,
  OverviewPartialNotice,
  OverviewStaleNotice,
  OverviewUnauthorizedState,
} from "@/components/overview/overview-states";
import { EnvironmentBadge } from "@/components/shell/environment-badge";
import { useSession } from "@/components/providers/session-provider";
import { usePlatformOverview } from "@/hooks/use-platform-overview";
import { isUnauthorizedError } from "@/lib/api/errors";
import { summarizeServiceStatuses } from "@/lib/status/map-service-status";
import type { ConsoleScenario } from "@/contracts/types/platform-health";

const EXPECTED_SERVICE_COUNT = 13;

function parseScenario(value: string | null): ConsoleScenario {
  switch (value) {
    case "empty":
    case "partial":
    case "stale":
    case "error":
    case "unauthorized":
    case "ok":
      return value;
    default:
      return "ok";
  }
}

export function OverviewPage() {
  const searchParams = useSearchParams();
  const scenario = parseScenario(searchParams.get("scenario"));
  const { session, signInBootstrap } = useSession();
  const query = usePlatformOverview(scenario);

  if (!session) {
    return <OverviewUnauthorizedState onSignIn={signInBootstrap} />;
  }

  if (query.isLoading || query.isPending) {
    return <OverviewLoadingState />;
  }

  if (query.isError) {
    if (isUnauthorizedError(query.error)) {
      return <OverviewUnauthorizedState onSignIn={signInBootstrap} />;
    }

    const message =
      query.error instanceof Error
        ? query.error.message
        : "Unknown overview failure.";

    return (
      <OverviewErrorState message={message} onRetry={() => query.refetch()} />
    );
  }

  const overview = query.data;
  if (!overview) {
    return <OverviewEmptyState />;
  }

  const summary = summarizeServiceStatuses(
    overview.services.map((service) => service.status),
  );
  const isPartial = overview.services.length < EXPECTED_SERVICE_COUNT;
  const isStalePayload =
    scenario === "stale" ||
    overview.services.every((service) => service.status === "stale");

  return (
    <div className="space-y-5" data-testid="overview-page">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="space-y-2">
          <p className="text-[11px] font-medium tracking-[0.14em] text-[color:var(--muted-fg)] uppercase">
            Operations
          </p>
          <h1 className="font-[family-name:var(--font-display)] text-3xl tracking-tight">
            Overview
          </h1>
          <p className="max-w-2xl text-sm text-[color:var(--muted-fg)]">
            Read-only infrastructure and platform health surface. Values come
            from the typed mock contract layer until live health APIs exist.
          </p>
        </div>
        <div className="flex flex-col items-end gap-2 text-right">
          <EnvironmentBadge environment={overview.environment} />
          <p className="font-[family-name:var(--font-mono)] text-xs text-[color:var(--muted-fg)]">
            Freshness window {overview.freshnessSeconds}s · Generated{" "}
            <time dateTime={overview.generatedAt}>{overview.generatedAt}</time>
          </p>
          <p className="text-xs text-[color:var(--muted-fg)]">
            {summary.healthy} healthy · {summary.attention} need attention ·{" "}
            {summary.total} total
          </p>
        </div>
      </div>

      {isPartial ? (
        <OverviewPartialNotice count={overview.services.length} />
      ) : null}
      {isStalePayload ? (
        <OverviewStaleNotice generatedAt={overview.generatedAt} />
      ) : null}

      {overview.services.length === 0 ? (
        <OverviewEmptyState />
      ) : (
        <div className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {overview.services.map((service) => (
              <ServiceStatusCard key={service.id} service={service} />
            ))}
          </div>
          <ServiceStatusTable services={overview.services} />
        </div>
      )}
    </div>
  );
}
