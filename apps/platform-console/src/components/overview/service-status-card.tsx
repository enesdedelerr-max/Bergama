import type { PlatformServiceHealth } from "@/contracts/types/platform-health";
import { EnvironmentBadge } from "@/components/shell/environment-badge";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { mapServiceStatus } from "@/lib/status/map-service-status";

function formatCheckedAt(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(date);
}

export function ServiceStatusCard({
  service,
}: {
  service: PlatformServiceHealth;
}) {
  const presentation = mapServiceStatus(service.status);

  return (
    <Card
      data-testid={`service-card-${service.id}`}
      data-status={service.status}
    >
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <CardTitle>{service.name}</CardTitle>
          <Badge tone={presentation.tone}>{presentation.label}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <dl className="grid gap-2 text-sm">
          <div className="flex items-center justify-between gap-3">
            <dt className="text-[color:var(--muted-fg)]">Environment</dt>
            <dd>
              <EnvironmentBadge environment={service.environment} />
            </dd>
          </div>
          <div className="flex items-center justify-between gap-3">
            <dt className="text-[color:var(--muted-fg)]">Version</dt>
            <dd className="font-[family-name:var(--font-mono)] text-xs">
              {service.version ?? "n/a"}
            </dd>
          </div>
          <div className="flex items-center justify-between gap-3">
            <dt className="text-[color:var(--muted-fg)]">Last checked</dt>
            <dd className="font-[family-name:var(--font-mono)] text-xs">
              <time dateTime={service.lastCheckedAt}>
                {formatCheckedAt(service.lastCheckedAt)} UTC
              </time>
            </dd>
          </div>
        </dl>
        <p className="text-sm text-[color:var(--muted-fg)]">
          {service.message}
        </p>
      </CardContent>
    </Card>
  );
}
