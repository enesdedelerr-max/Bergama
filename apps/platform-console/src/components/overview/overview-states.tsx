import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function OverviewLoadingState() {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label="Loading platform overview"
      className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"
    >
      {Array.from({ length: 6 }).map((_, index) => (
        <Card key={index}>
          <CardHeader>
            <Skeleton className="h-4 w-1/2" />
          </CardHeader>
          <CardContent className="space-y-3">
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-4/5" />
            <Skeleton className="h-3 w-3/5" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export function OverviewEmptyState() {
  return (
    <Card data-testid="overview-empty">
      <CardHeader>
        <CardTitle>No services reported</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-[color:var(--muted-fg)]">
          The overview contract returned an empty service list. Nothing is
          available to display.
        </p>
      </CardContent>
    </Card>
  );
}

export function OverviewErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <Card data-testid="overview-error" role="alert">
      <CardHeader>
        <CardTitle>Overview unavailable</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-[color:var(--muted-fg)]">{message}</p>
        <Button onClick={onRetry}>Retry</Button>
      </CardContent>
    </Card>
  );
}

export function OverviewUnauthorizedState({
  onSignIn,
}: {
  onSignIn: () => void;
}) {
  return (
    <Card data-testid="overview-unauthorized" role="alert">
      <CardHeader>
        <CardTitle>Unauthorized</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-[color:var(--muted-fg)]">
          A local bootstrap session is required to view platform health.
        </p>
        <Button onClick={onSignIn}>Restore bootstrap session</Button>
      </CardContent>
    </Card>
  );
}

export function OverviewPartialNotice({ count }: { count: number }) {
  return (
    <div
      data-testid="overview-partial"
      className="rounded-sm border border-[color:var(--status-warning-border)] bg-[color:var(--status-warning-bg)] px-3 py-2 text-sm text-[color:var(--status-warning-fg)]"
      role="status"
    >
      Partial inventory: only {count} services were returned by the overview
      contract.
    </div>
  );
}

export function OverviewStaleNotice({ generatedAt }: { generatedAt: string }) {
  return (
    <div
      data-testid="overview-stale"
      className="rounded-sm border border-[color:var(--status-info-border)] bg-[color:var(--status-info-bg)] px-3 py-2 text-sm text-[color:var(--status-info-fg)]"
      role="status"
    >
      Stale overview data. Last generated at{" "}
      <time dateTime={generatedAt}>{generatedAt}</time>.
    </div>
  );
}
