import { describe, expect, it } from "vitest";
import {
  HR_RECORDED_PAYLOAD_MAX_LENGTH,
  inspectHrRecordedPayload,
} from "@/lib/premarket/hr-payload";

describe("inspectHrRecordedPayload", () => {
  it("accepts valid payload within the 8192 limit", () => {
    const result = inspectHrRecordedPayload("attestation-text");
    expect(result).toEqual({ kind: "valid", text: "attestation-text" });
  });

  it("accepts empty string as empty", () => {
    expect(inspectHrRecordedPayload("")).toEqual({ kind: "empty", text: "" });
  });

  it("rejects oversized payload without truncating for render", () => {
    const oversized = "a".repeat(HR_RECORDED_PAYLOAD_MAX_LENGTH + 1);
    expect(inspectHrRecordedPayload(oversized)).toEqual({
      kind: "oversized",
      length: HR_RECORDED_PAYLOAD_MAX_LENGTH + 1,
    });
  });

  it("rejects non-string values", () => {
    expect(inspectHrRecordedPayload({ nested: true })).toEqual({
      kind: "invalid",
      reason: "not_string",
    });
  });

  it("accepts payload at exactly the maximum length", () => {
    const exact = "b".repeat(HR_RECORDED_PAYLOAD_MAX_LENGTH);
    const result = inspectHrRecordedPayload(exact);
    expect(result.kind).toBe("valid");
    if (result.kind === "valid") {
      expect(result.text.length).toBe(HR_RECORDED_PAYLOAD_MAX_LENGTH);
    }
  });
});
