export type PlatformEnvironment = "paper" | "sandbox" | "live";

export type ServiceHealthStatus =
  "healthy" | "degraded" | "unavailable" | "unknown" | "stale";

export type PlatformServiceId =
  | "kubernetes"
  | "argocd"
  | "postgresql"
  | "redis"
  | "kafka"
  | "clickhouse"
  | "minio"
  | "iceberg"
  | "prometheus"
  | "grafana"
  | "loki"
  | "tempo"
  | "sprint1-gate";

export type PlatformServiceHealth = {
  id: PlatformServiceId;
  name: string;
  status: ServiceHealthStatus;
  environment: PlatformEnvironment;
  version: string | null;
  lastCheckedAt: string;
  message: string;
};

export type PlatformOverviewResponse = {
  generatedAt: string;
  environment: PlatformEnvironment;
  services: PlatformServiceHealth[];
  freshnessSeconds: number;
};

export type ConsoleScenario =
  "ok" | "empty" | "partial" | "stale" | "error" | "unauthorized";
