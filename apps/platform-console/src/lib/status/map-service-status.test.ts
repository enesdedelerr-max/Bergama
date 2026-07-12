import { describe, expect, it } from "vitest";
import {
  isAttentionStatus,
  mapServiceStatus,
  summarizeServiceStatuses,
} from "@/lib/status/map-service-status";
import type { ServiceHealthStatus } from "@/contracts/types/platform-health";

describe("mapServiceStatus", () => {
  const cases: Array<[ServiceHealthStatus, string]> = [
    ["healthy", "Healthy"],
    ["degraded", "Degraded"],
    ["unavailable", "Unavailable"],
    ["unknown", "Unknown"],
    ["stale", "Stale"],
  ];

  it.each(cases)("maps %s to label %s", (status, label) => {
    expect(mapServiceStatus(status).label).toBe(label);
  });

  it("marks non-healthy statuses as attention", () => {
    expect(isAttentionStatus("healthy")).toBe(false);
    expect(isAttentionStatus("degraded")).toBe(true);
    expect(isAttentionStatus("stale")).toBe(true);
  });

  it("summarizes healthy versus attention counts", () => {
    expect(
      summarizeServiceStatuses([
        "healthy",
        "healthy",
        "degraded",
        "stale",
        "unavailable",
      ]),
    ).toEqual({ healthy: 2, attention: 3, total: 5 });
  });
});
