/**
 * Canonical Premarket / intelligence-run query keys.
 * Must never embed bearer tokens.
 */
export const intelligenceRunQueryKeys = {
  all: ["intelligence-runs"] as const,
  latestDashboardCapable: ["intelligence-runs", "latest-dashboard-capable"] as const,
  byId: (runId: string) => ["intelligence-runs", "id", runId] as const,
  byFingerprint: (fingerprint: string) =>
    ["intelligence-runs", "fingerprint", fingerprint] as const,
  dashboard: (runId: string) =>
    ["intelligence-runs", "id", runId, "dashboard"] as const,
  humanReview: (runId: string) =>
    ["intelligence-runs", "id", runId, "human-review"] as const,
  ade: (runId: string) => ["intelligence-runs", "id", runId, "ade"] as const,
} as const;

export function assertQueryKeyHasNoBearerToken(
  key: readonly unknown[],
  token: string | null | undefined,
): void {
  if (!token) {
    return;
  }
  const serialized = JSON.stringify(key);
  if (serialized.includes(token)) {
    throw new Error("query key must not contain bearer token");
  }
}
