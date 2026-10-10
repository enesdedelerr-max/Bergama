import { describe, expect, it } from "vitest";
import { ApiClientError } from "@/lib/api/errors";
import { mapProductErrorToUxState } from "@/lib/premarket/map-product-error";
import { PREMARKET_UX_STATES } from "@/lib/premarket/ux-states";

describe("mapProductErrorToUxState", () => {
  it("exposes exactly 18 frozen UX state IDs", () => {
    expect(PREMARKET_UX_STATES).toHaveLength(18);
    expect(PREMARKET_UX_STATES).toEqual([
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
    ]);
  });

  it("maps run_not_found", () => {
    expect(
      mapProductErrorToUxState(
        new ApiClientError(
          "intelligence.runs.run_not_found",
          "missing",
          404,
          "req-1",
        ),
        "run",
      ),
    ).toBe("run_not_found");
  });

  it("maps stage_not_present by endpoint", () => {
    const error = new ApiClientError(
      "intelligence.runs.stage_not_present",
      "absent",
      404,
      "req-2",
    );
    expect(mapProductErrorToUxState(error, "human_review")).toBe(
      "human_review_absent",
    );
    expect(mapProductErrorToUxState(error, "ade")).toBe("ade_absent");
  });

  it("maps unsupported, corrupt, and storage codes", () => {
    expect(
      mapProductErrorToUxState(
        new ApiClientError(
          "intelligence.runs.unsupported_snapshot_contract",
          "bad",
          422,
          null,
        ),
        "run",
      ),
    ).toBe("unsupported_snapshot_contract");
    expect(
      mapProductErrorToUxState(
        new ApiClientError(
          "intelligence.runs.corrupt_persisted_snapshot",
          "bad",
          500,
          null,
        ),
        "run",
      ),
    ).toBe("corrupt_persisted_snapshot");
    expect(
      mapProductErrorToUxState(
        new ApiClientError(
          "intelligence.runs.storage_unavailable",
          "down",
          503,
          null,
        ),
        "latest",
      ),
    ).toBe("storage_unavailable");
  });

  it("maps insufficient scope and network failures", () => {
    expect(
      mapProductErrorToUxState(
        new ApiClientError("authz.insufficient_scope", "denied", 403, null),
        "latest",
      ),
    ).toBe("insufficient_scope");
    expect(mapProductErrorToUxState(new TypeError("fetch failed"), "latest")).toBe(
      "network_unavailable",
    );
  });

  it("maps latest 404 without product code to latest_absent", () => {
    expect(
      mapProductErrorToUxState(
        new ApiClientError("not.found", "missing", 404, null),
        "latest",
      ),
    ).toBe("latest_absent");
  });

  it("does not invent a UX state for 401 (auth-owned)", () => {
    expect(
      mapProductErrorToUxState(
        new ApiClientError("auth.unauthorized", "unauth", 401, null),
        "run",
      ),
    ).toBeNull();
  });
});
