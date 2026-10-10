/**
 * Frozen Premarket UX semantic state IDs (Sprint 15 WS2).
 * Literal copy is not frozen; semantic identity is.
 */

export const PREMARKET_UX_STATES = [
  "auth_loading",
  "unauthenticated",
  "auth_expired",
  "bootstrap_disabled",
  "bootstrap_failed",
  "insufficient_scope",
  "latest_loading",
  "latest_absent",
  "run_not_found",
  "dashboard_present",
  "human_review_absent",
  "ade_absent",
  "unsupported_snapshot_contract",
  "corrupt_persisted_snapshot",
  "storage_unavailable",
  "network_unavailable",
  "refreshing",
  "success",
] as const;

export type PremarketUxState = (typeof PREMARKET_UX_STATES)[number];

export const PIPELINE_FINGERPRINT_HEX_LENGTH = 64;

const LOWER_HEX = /^[0-9a-f]+$/;

/** Normalize and validate a 64-char lowercase hex pipeline fingerprint. */
export function normalizePipelineFingerprint(
  raw: string,
): { ok: true; fingerprint: string } | { ok: false; reason: "empty" | "invalid" } {
  const trimmed = raw.trim().toLowerCase();
  if (trimmed.length === 0) {
    return { ok: false, reason: "empty" };
  }
  if (
    trimmed.length !== PIPELINE_FINGERPRINT_HEX_LENGTH ||
    !LOWER_HEX.test(trimmed)
  ) {
    return { ok: false, reason: "invalid" };
  }
  return { ok: true, fingerprint: trimmed };
}
