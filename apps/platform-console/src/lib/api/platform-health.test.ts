import { describe, expect, it } from "vitest";
import { buildMockOverview } from "@/lib/api/platform-health";

describe("buildMockOverview", () => {
  it("returns the full service inventory for ok scenario", () => {
    const overview = buildMockOverview("ok");
    expect(overview.services).toHaveLength(13);
    expect(overview.environment).toBe("paper");
    expect(overview.services.map((service) => service.id)).toContain(
      "sprint1-gate",
    );
  });

  it("returns an empty inventory for empty scenario", () => {
    expect(buildMockOverview("empty").services).toHaveLength(0);
  });

  it("returns a reduced inventory for partial scenario", () => {
    expect(buildMockOverview("partial").services.length).toBeLessThan(13);
  });

  it("marks all services stale for stale scenario", () => {
    const overview = buildMockOverview("stale");
    expect(
      overview.services.every((service) => service.status === "stale"),
    ).toBe(true);
  });
});
