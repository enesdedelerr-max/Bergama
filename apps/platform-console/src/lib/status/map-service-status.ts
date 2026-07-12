import type { ServiceHealthStatus } from "@/contracts/types/platform-health";

export type StatusPresentation = {
  label: string;
  tone: "success" | "warning" | "danger" | "muted" | "info";
  description: string;
};

const STATUS_PRESENTATION: Record<ServiceHealthStatus, StatusPresentation> = {
  healthy: {
    label: "Healthy",
    tone: "success",
    description: "Service reports a healthy state.",
  },
  degraded: {
    label: "Degraded",
    tone: "warning",
    description: "Service is reachable but operating below expectations.",
  },
  unavailable: {
    label: "Unavailable",
    tone: "danger",
    description: "Service is not reachable or not serving traffic.",
  },
  unknown: {
    label: "Unknown",
    tone: "muted",
    description: "Health could not be determined.",
  },
  stale: {
    label: "Stale",
    tone: "info",
    description: "Last successful check is older than the freshness window.",
  },
};

export function mapServiceStatus(
  status: ServiceHealthStatus,
): StatusPresentation {
  return STATUS_PRESENTATION[status];
}

export function isAttentionStatus(status: ServiceHealthStatus): boolean {
  return (
    status === "degraded" ||
    status === "unavailable" ||
    status === "unknown" ||
    status === "stale"
  );
}

export function summarizeServiceStatuses(statuses: ServiceHealthStatus[]): {
  healthy: number;
  attention: number;
  total: number;
} {
  const attention = statuses.filter(isAttentionStatus).length;
  return {
    healthy: statuses.length - attention,
    attention,
    total: statuses.length,
  };
}
