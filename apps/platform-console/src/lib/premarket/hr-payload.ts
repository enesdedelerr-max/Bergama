/** Maximum characters authorized for Human Review recorded_payload rendering. */
export const HR_RECORDED_PAYLOAD_MAX_LENGTH = 8192;

export type HrPayloadInspection =
  | { kind: "valid"; text: string }
  | { kind: "empty"; text: "" }
  | { kind: "oversized"; length: number }
  | { kind: "invalid"; reason: "not_string" };

/**
 * Inspect untrusted Human Review recorded_payload for safe React text rendering.
 * Does not HTML-sanitize; callers must render as React escaped text only.
 */
export function inspectHrRecordedPayload(value: unknown): HrPayloadInspection {
  if (typeof value !== "string") {
    return { kind: "invalid", reason: "not_string" };
  }
  if (value.length === 0) {
    return { kind: "empty", text: "" };
  }
  if (value.length > HR_RECORDED_PAYLOAD_MAX_LENGTH) {
    return { kind: "oversized", length: value.length };
  }
  return { kind: "valid", text: value };
}
