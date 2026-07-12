import type {
  ConsoleScenario,
  PlatformOverviewResponse,
  PlatformServiceHealth,
} from "@/contracts/types/platform-health";
import { ApiClientError } from "@/lib/api/errors";

const FIXED_CHECKED_AT = "2026-07-12T20:00:00.000Z";
const STALE_CHECKED_AT = "2026-07-12T18:00:00.000Z";

const BASE_SERVICES: PlatformServiceHealth[] = [
  {
    id: "kubernetes",
    name: "Kubernetes",
    status: "healthy",
    environment: "paper",
    version: "v1.32.2",
    lastCheckedAt: FIXED_CHECKED_AT,
    message: "Control plane ready; worker nodes Ready.",
  },
  {
    id: "argocd",
    name: "ArgoCD",
    status: "healthy",
    environment: "paper",
    version: "v2.14.9",
    lastCheckedAt: FIXED_CHECKED_AT,
    message: "Applications Healthy and Synced.",
  },
  {
    id: "postgresql",
    name: "PostgreSQL",
    status: "healthy",
    environment: "paper",
    version: "16.8",
    lastCheckedAt: FIXED_CHECKED_AT,
    message: "Primary accepting connections.",
  },
  {
    id: "redis",
    name: "Redis",
    status: "degraded",
    environment: "paper",
    version: "7.4.2",
    lastCheckedAt: FIXED_CHECKED_AT,
    message: "Memory pressure above soft limit.",
  },
  {
    id: "kafka",
    name: "Kafka",
    status: "healthy",
    environment: "paper",
    version: "3.9.0",
    lastCheckedAt: FIXED_CHECKED_AT,
    message: "KRaft quorum stable.",
  },
  {
    id: "clickhouse",
    name: "ClickHouse",
    status: "healthy",
    environment: "paper",
    version: "25.3.2",
    lastCheckedAt: FIXED_CHECKED_AT,
    message: "Query endpoint responding.",
  },
  {
    id: "minio",
    name: "MinIO",
    status: "healthy",
    environment: "paper",
    version: "RELEASE.2025-04-22",
    lastCheckedAt: FIXED_CHECKED_AT,
    message: "Object API healthy.",
  },
  {
    id: "iceberg",
    name: "Iceberg",
    status: "unknown",
    environment: "paper",
    version: null,
    lastCheckedAt: FIXED_CHECKED_AT,
    message: "Catalog probe not configured.",
  },
  {
    id: "prometheus",
    name: "Prometheus",
    status: "healthy",
    environment: "paper",
    version: "v3.2.1",
    lastCheckedAt: FIXED_CHECKED_AT,
    message: "Scrape targets up.",
  },
  {
    id: "grafana",
    name: "Grafana",
    status: "healthy",
    environment: "paper",
    version: "11.6.0",
    lastCheckedAt: FIXED_CHECKED_AT,
    message: "UI and datasource health OK.",
  },
  {
    id: "loki",
    name: "Loki",
    status: "stale",
    environment: "paper",
    version: "3.4.2",
    lastCheckedAt: STALE_CHECKED_AT,
    message: "Last successful check exceeded freshness window.",
  },
  {
    id: "tempo",
    name: "Tempo",
    status: "unavailable",
    environment: "paper",
    version: "2.7.1",
    lastCheckedAt: FIXED_CHECKED_AT,
    message: "Distributor endpoint timed out.",
  },
  {
    id: "sprint1-gate",
    name: "Sprint 1 Gate",
    status: "degraded",
    environment: "paper",
    version: "v0.1.0-sprint1",
    lastCheckedAt: FIXED_CHECKED_AT,
    message: "Gate incomplete; make gate-sprint1 has not passed.",
  },
];

function cloneServices(
  services: PlatformServiceHealth[],
): PlatformServiceHealth[] {
  return services.map((service) => ({ ...service }));
}

export function buildMockOverview(
  scenario: ConsoleScenario = "ok",
): PlatformOverviewResponse {
  switch (scenario) {
    case "empty":
      return {
        generatedAt: FIXED_CHECKED_AT,
        environment: "paper",
        services: [],
        freshnessSeconds: 60,
      };
    case "partial":
      return {
        generatedAt: FIXED_CHECKED_AT,
        environment: "paper",
        services: cloneServices(BASE_SERVICES).slice(0, 5),
        freshnessSeconds: 60,
      };
    case "stale":
      return {
        generatedAt: STALE_CHECKED_AT,
        environment: "paper",
        services: cloneServices(BASE_SERVICES).map((service) => ({
          ...service,
          status: "stale",
          lastCheckedAt: STALE_CHECKED_AT,
          message: "Overview payload exceeded freshness window.",
        })),
        freshnessSeconds: 60,
      };
    case "ok":
    default:
      return {
        generatedAt: FIXED_CHECKED_AT,
        environment: "paper",
        services: cloneServices(BASE_SERVICES),
        freshnessSeconds: 60,
      };
  }
}

export type FetchPlatformOverviewOptions = {
  scenario?: ConsoleScenario;
  signal?: AbortSignal;
};

/**
 * Typed mock contract client for the Platform Operations Console shell.
 * This is an explicit local mock layer — not a live infrastructure integration.
 */
export async function fetchPlatformOverview(
  options: FetchPlatformOverviewOptions = {},
): Promise<PlatformOverviewResponse> {
  const scenario = options.scenario ?? "ok";

  if (options.signal?.aborted) {
    throw new DOMException("Aborted", "AbortError");
  }

  if (scenario === "unauthorized") {
    throw new ApiClientError(
      "console.unauthorized",
      "Local bootstrap session is missing or expired.",
      401,
    );
  }

  if (scenario === "error") {
    throw new ApiClientError(
      "console.overview.unavailable",
      "Platform overview mock contract failed to load.",
      503,
    );
  }

  return buildMockOverview(scenario);
}
