import { describe, expect, it } from "vitest";
import { CONSOLE_NAV } from "@/components/shell/nav-items";

describe("CONSOLE_NAV Premarket entry", () => {
  it("includes exactly one Premarket entry at /premarket", () => {
    const premarket = CONSOLE_NAV.filter((item) => item.label === "Premarket");
    expect(premarket).toHaveLength(1);
    expect(premarket[0]).toEqual({ href: "/premarket", label: "Premarket" });
  });

  it("preserves Overview and Settings without redesign", () => {
    expect(CONSOLE_NAV[0]).toEqual({ href: "/", label: "Overview" });
    expect(CONSOLE_NAV[CONSOLE_NAV.length - 1]).toEqual({
      href: "/settings",
      label: "Settings",
    });
  });
});
