"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiClientError } from "@/lib/api/errors";
import type { PremarketUxState } from "@/lib/premarket/ux-states";

export function PremarketAuthLoadingState() {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label="Authenticating product access"
      data-ux-state="auth_loading"
      className="space-y-3"
    >
      <Skeleton className="h-6 w-48" />
      <Skeleton className="h-20 w-full" />
    </div>
  );
}

export function PremarketUnauthenticatedState({
  onAcquire,
}: {
  onAcquire: () => void;
}) {
  return (
    <Card data-ux-state="unauthenticated" role="alert">
      <CardHeader>
        <CardTitle>Product authentication required</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-[color:var(--muted-fg)]">
          Premarket reads require a product API bearer token with
          intelligence:runs:read. Console mock session does not authorize
          product access.
        </p>
        <Button type="button" onClick={onAcquire}>
          Acquire bootstrap token
        </Button>
      </CardContent>
    </Card>
  );
}

export function PremarketAuthExpiredState({
  onAcquire,
}: {
  onAcquire: () => void;
}) {
  return (
    <Card data-ux-state="auth_expired" role="alert">
      <CardHeader>
        <CardTitle>Product token expired</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-[color:var(--muted-fg)]">
          The in-memory product token is no longer valid.
        </p>
        <Button type="button" onClick={onAcquire}>
          Reacquire bootstrap token
        </Button>
      </CardContent>
    </Card>
  );
}

export function PremarketBootstrapDisabledState() {
  return (
    <Card data-ux-state="bootstrap_disabled" role="alert">
      <CardHeader>
        <CardTitle>Bootstrap disabled</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-[color:var(--muted-fg)]">
          Bootstrap token issuance is disabled in this environment. Premarket
          product reads cannot proceed.
        </p>
      </CardContent>
    </Card>
  );
}

export function PremarketBootstrapFailedState({
  onAcquire,
}: {
  onAcquire: () => void;
}) {
  return (
    <Card data-ux-state="bootstrap_failed" role="alert">
      <CardHeader>
        <CardTitle>Bootstrap failed</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-[color:var(--muted-fg)]">
          Product bootstrap authentication failed. No Premarket data is shown.
        </p>
        <Button type="button" onClick={onAcquire}>
          Retry bootstrap
        </Button>
      </CardContent>
    </Card>
  );
}

export function PremarketInsufficientScopeState() {
  return (
    <Card data-ux-state="insufficient_scope" role="alert">
      <CardHeader>
        <CardTitle>Insufficient scope</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-[color:var(--muted-fg)]">
          The product token lacks intelligence:runs:read. Token is retained;
          bootstrap is not attempted for this condition.
        </p>
      </CardContent>
    </Card>
  );
}

export function PremarketLatestLoadingState() {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label="Loading latest dashboard-capable run"
      data-ux-state="latest_loading"
      className="space-y-3"
    >
      <Skeleton className="h-5 w-64" />
      <Skeleton className="h-24 w-full" />
    </div>
  );
}

export function PremarketLatestAbsentState() {
  return (
    <Card data-ux-state="latest_absent" data-testid="premarket-latest-absent">
      <CardHeader>
        <CardTitle>No latest dashboard-capable run</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-[color:var(--muted-fg)]">
          No persisted dashboard-capable intelligence run is available. Use
          run ID or fingerprint lookup to open an existing run.
        </p>
      </CardContent>
    </Card>
  );
}

export function PremarketRunNotFoundState() {
  return (
    <Card data-ux-state="run_not_found" role="alert" data-testid="premarket-run-not-found">
      <CardHeader>
        <CardTitle>Run not found</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-[color:var(--muted-fg)]">
          No persisted intelligence run matches the requested identity.
        </p>
      </CardContent>
    </Card>
  );
}

export function PremarketStageAbsentState({
  state,
  label,
}: {
  state: "human_review_absent" | "ade_absent";
  label: string;
}) {
  return (
    <Card data-ux-state={state} data-testid={`premarket-${state}`}>
      <CardHeader>
        <CardTitle>{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-[color:var(--muted-fg)]">
          This stage is not present on the persisted run snapshot.
        </p>
      </CardContent>
    </Card>
  );
}

export function PremarketProductFaultState({
  state,
  title,
  error,
}: {
  state: Extract<
    PremarketUxState,
    | "unsupported_snapshot_contract"
    | "corrupt_persisted_snapshot"
    | "storage_unavailable"
    | "network_unavailable"
  >;
  title: string;
  error?: unknown;
}) {
  const product =
    error instanceof ApiClientError
      ? {
          code: error.code,
          message: error.message,
          request_id: error.requestId,
        }
      : null;

  return (
    <Card data-ux-state={state} role="alert" data-testid={`premarket-${state}`}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <p className="text-sm text-[color:var(--muted-fg)]">
          Premarket cannot display this product result. No substitute data is
          shown.
        </p>
        {product ? (
          <dl className="grid gap-1 text-xs text-[color:var(--muted-fg)]">
            <div>
              <dt className="inline font-medium">code: </dt>
              <dd className="inline font-mono">{product.code}</dd>
            </div>
            <div>
              <dt className="inline font-medium">message: </dt>
              <dd className="inline">{product.message}</dd>
            </div>
            {product.request_id ? (
              <div>
                <dt className="inline font-medium">request_id: </dt>
                <dd className="inline font-mono">{product.request_id}</dd>
              </div>
            ) : null}
          </dl>
        ) : null}
      </CardContent>
    </Card>
  );
}

export function PremarketRefreshingNotice() {
  return (
    <p
      role="status"
      aria-live="polite"
      data-ux-state="refreshing"
      className="text-xs text-[color:var(--muted-fg)]"
    >
      Refreshing persisted product data…
    </p>
  );
}

export function PremarketFailClosedError({ error }: { error: unknown }) {
  const product =
    error instanceof ApiClientError
      ? {
          code: error.code,
          message: error.message,
          request_id: error.requestId,
        }
      : {
          code: "product_error.unknown",
          message:
            error instanceof Error
              ? error.message
              : "Unknown product failure",
          request_id: null as string | null,
        };

  return (
    <Card role="alert" data-testid="premarket-fail-closed">
      <CardHeader>
        <CardTitle>Product error</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid gap-1 text-xs text-[color:var(--muted-fg)]">
          <div>
            <dt className="inline font-medium">code: </dt>
            <dd className="inline font-mono">{product.code}</dd>
          </div>
          <div>
            <dt className="inline font-medium">message: </dt>
            <dd className="inline">{product.message}</dd>
          </div>
          {product.request_id ? (
            <div>
              <dt className="inline font-medium">request_id: </dt>
              <dd className="inline font-mono">{product.request_id}</dd>
            </div>
          ) : null}
        </dl>
      </CardContent>
    </Card>
  );
}
