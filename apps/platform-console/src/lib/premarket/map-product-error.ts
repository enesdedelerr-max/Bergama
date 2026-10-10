import { ApiClientError, isAbortError } from "@/lib/api/errors";
import type { PremarketUxState } from "@/lib/premarket/ux-states";

export type ProductErrorEndpoint =
  | "latest"
  | "run"
  | "dashboard"
  | "human_review"
  | "ade"
  | "fingerprint";

/**
 * Map ProductErrorResponse / transport failures to frozen Premarket UX states.
 * Does not invent backend codes. Unknown product errors fail closed via null
 * (caller should present fail-closed product error UI without fabricated data).
 */
export function mapProductErrorToUxState(
  error: unknown,
  endpoint: ProductErrorEndpoint,
): PremarketUxState | null {
  if (isAbortError(error)) {
    return null;
  }

  if (!(error instanceof ApiClientError)) {
    // Network / transport failure outside structured product errors.
    if (error instanceof TypeError || error instanceof Error) {
      return "network_unavailable";
    }
    return "network_unavailable";
  }

  const { code, status } = error;

  if (status === 403 || code === "authz.insufficient_scope") {
    return "insufficient_scope";
  }

  // 401 is owned by WS1 auth recovery; Premarket surfaces resulting auth UX.
  if (status === 401) {
    return null;
  }

  switch (code) {
    case "intelligence.runs.run_not_found":
      return "run_not_found";
    case "intelligence.runs.unsupported_snapshot_contract":
      return "unsupported_snapshot_contract";
    case "intelligence.runs.corrupt_persisted_snapshot":
      return "corrupt_persisted_snapshot";
    case "intelligence.runs.storage_unavailable":
      return "storage_unavailable";
    case "intelligence.runs.stage_not_present":
      if (endpoint === "human_review") {
        return "human_review_absent";
      }
      if (endpoint === "ade") {
        return "ade_absent";
      }
      return null;
    case "intelligence.runs.invalid_identifier":
      if (endpoint === "fingerprint" || endpoint === "run") {
        return "run_not_found";
      }
      return null;
    default:
      break;
  }

  if (status === 404) {
    if (endpoint === "latest") {
      return "latest_absent";
    }
    if (endpoint === "human_review") {
      return "human_review_absent";
    }
    if (endpoint === "ade") {
      return "ade_absent";
    }
    if (
      endpoint === "run" ||
      endpoint === "fingerprint" ||
      endpoint === "dashboard"
    ) {
      return "run_not_found";
    }
  }

  if (status === 503) {
    return "storage_unavailable";
  }

  if (status === 0 || status >= 500) {
    // Unstructured / server failure — fail closed; prefer storage when 503 above.
    return null;
  }

  return null;
}

export function isNetworkTransportError(error: unknown): boolean {
  if (error instanceof ApiClientError) {
    return false;
  }
  return error instanceof TypeError || error instanceof Error;
}
