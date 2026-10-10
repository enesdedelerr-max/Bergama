import { describe, expect, it } from "vitest";
import {
  assertQueryKeyHasNoBearerToken,
  intelligenceRunQueryKeys,
} from "@/lib/api/query-keys";
import {
  createPlatformQueryClient,
  QUERY_GC_TIME_MS,
  QUERY_STALE_TIME_MS,
} from "@/components/providers/query-provider";
import { ApiClientError } from "@/lib/api/errors";
import { clearProductQueryCache } from "@/lib/api/product-cache";

describe("query foundation", () => {
  it("exposes canonical keys without bearer tokens", () => {
    const token = "secret-token-value";
    const keys = [
      intelligenceRunQueryKeys.latestDashboardCapable,
      intelligenceRunQueryKeys.byId("run-1"),
      intelligenceRunQueryKeys.byFingerprint("fp"),
      intelligenceRunQueryKeys.dashboard("run-1"),
      intelligenceRunQueryKeys.humanReview("run-1"),
      intelligenceRunQueryKeys.ade("run-1"),
    ];
    for (const key of keys) {
      assertQueryKeyHasNoBearerToken(key, token);
      expect(JSON.stringify(key)).not.toContain(token);
    }
  });

  it("applies frozen QueryClient defaults and retry matrix", async () => {
    const client = createPlatformQueryClient();
    const defaults = client.getDefaultOptions().queries;
    expect(defaults?.staleTime).toBe(QUERY_STALE_TIME_MS);
    expect(defaults?.gcTime).toBe(QUERY_GC_TIME_MS);
    expect(defaults?.refetchOnWindowFocus).toBe(false);
    expect(defaults?.refetchOnReconnect).toBe(false);
    expect(defaults?.refetchInterval).toBe(false);

    const retry = defaults?.retry;
    expect(typeof retry).toBe("function");
    if (typeof retry !== "function") {
      return;
    }
    expect(retry(0, new ApiClientError("x", "y", 401))).toBe(false);
    expect(retry(0, new ApiClientError("x", "y", 403))).toBe(false);
    expect(retry(0, new ApiClientError("x", "y", 500))).toBe(false);
    expect(retry(0, new ApiClientError("x", "y", 503))).toBe(true);
    expect(retry(1, new ApiClientError("x", "y", 503))).toBe(false);
    expect(retry(0, new Error("network"))).toBe(true);
    expect(retry(1, new Error("network"))).toBe(false);
    expect(retry(0, new DOMException("Aborted", "AbortError"))).toBe(false);
  });

  it("clears product cache by intelligence-runs prefix", () => {
    const client = createPlatformQueryClient();
    client.setQueryData(intelligenceRunQueryKeys.latestDashboardCapable, {
      ok: true,
    });
    client.setQueryData(["other"], { keep: true });
    clearProductQueryCache(client);
    expect(
      client.getQueryData(intelligenceRunQueryKeys.latestDashboardCapable),
    ).toBeUndefined();
    expect(client.getQueryData(["other"])).toEqual({ keep: true });
  });
});
