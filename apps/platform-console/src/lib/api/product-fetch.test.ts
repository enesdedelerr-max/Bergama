import { describe, expect, it, vi } from "vitest";
import { ApiClientError } from "@/lib/api/errors";
import { productFetch } from "@/lib/api/product-fetch";

const baseDeps = {
  getAccessToken: () => "tok-123",
  getAuthGeneration: () => 1,
  reacquireOnce: async () => false,
  onForbidden: () => undefined,
  apiBaseUrl: "http://localhost:8000",
};

describe("productFetch", () => {
  it("uses credentials omit and injects Bearer when authenticated", async () => {
    const fetchImpl = vi.fn(async () => new Response("{}", { status: 200 }));
    await productFetch(
      "/api/v1/intelligence/runs/latest-dashboard-capable",
      { method: "GET" },
      {
        ...baseDeps,
        fetchImpl: fetchImpl as unknown as typeof fetch,
      },
    );
    expect(fetchImpl).toHaveBeenCalledTimes(1);
    const [, init] = fetchImpl.mock.calls[0] as unknown as [
      string,
      RequestInit,
    ];
    expect(init.credentials).toBe("omit");
    expect((init.headers as Record<string, string>).Authorization).toBe(
      "Bearer tok-123",
    );
  });

  it("propagates AbortSignal", async () => {
    const controller = new AbortController();
    const fetchImpl = vi.fn(async (_url, init) => {
      expect(init?.signal).toBe(controller.signal);
      return new Response("{}", { status: 200 });
    });
    await productFetch(
      "/api/v1/intelligence/runs/latest-dashboard-capable",
      { method: "GET", signal: controller.signal },
      {
        ...baseDeps,
        getAccessToken: () => null,
        fetchImpl: fetchImpl as unknown as typeof fetch,
      },
    );
    expect(fetchImpl).toHaveBeenCalledTimes(1);
  });

  it("maps ProductErrorResponse on non-auth failures", async () => {
    const fetchImpl = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            code: "run_not_found",
            message: "missing",
            request_id: "req-1",
          }),
          { status: 404 },
        ),
    );
    const response = await productFetch(
      "/api/v1/intelligence/runs/id/x",
      { method: "GET" },
      {
        ...baseDeps,
        getAccessToken: () => "tok",
        fetchImpl: fetchImpl as unknown as typeof fetch,
      },
    );
    expect(response.status).toBe(404);
  });

  it("passes request generation to reacquireOnce and replays once on 401", async () => {
    let calls = 0;
    const reacquireOnce = vi.fn(async () => true);
    const fetchImpl = vi.fn(async () => {
      calls += 1;
      if (calls === 1) {
        return new Response(
          JSON.stringify({
            code: "auth.expired",
            message: "expired",
            request_id: "r1",
          }),
          { status: 401 },
        );
      }
      return new Response("{}", { status: 200 });
    });
    const response = await productFetch(
      "/api/v1/intelligence/runs/latest-dashboard-capable",
      { method: "GET" },
      {
        ...baseDeps,
        getAccessToken: () => "old",
        getAuthGeneration: () => 7,
        reacquireOnce,
        fetchImpl: fetchImpl as unknown as typeof fetch,
      },
    );
    expect(response.status).toBe(200);
    expect(reacquireOnce).toHaveBeenCalledTimes(1);
    expect(reacquireOnce).toHaveBeenCalledWith(7);
    expect(fetchImpl).toHaveBeenCalledTimes(2);
  });

  it("does not recurse when replay also returns 401", async () => {
    const reacquireOnce = vi.fn(async () => true);
    const fetchImpl = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            code: "auth.expired",
            message: "expired",
            request_id: "r1",
          }),
          { status: 401 },
        ),
    );
    await expect(
      productFetch(
        "/api/v1/intelligence/runs/latest-dashboard-capable",
        { method: "GET" },
        {
          ...baseDeps,
          getAccessToken: () => "old",
          reacquireOnce,
          fetchImpl: fetchImpl as unknown as typeof fetch,
        },
      ),
    ).rejects.toBeInstanceOf(ApiClientError);
    expect(reacquireOnce).toHaveBeenCalledTimes(1);
    expect(fetchImpl).toHaveBeenCalledTimes(2);
  });

  it("on 403 retains flow to onForbidden without reacquire", async () => {
    const onForbidden = vi.fn();
    const reacquireOnce = vi.fn(async () => true);
    const fetchImpl = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            code: "authz.insufficient_scope",
            message: "scope",
            request_id: "r1",
          }),
          { status: 403 },
        ),
    );
    await expect(
      productFetch(
        "/api/v1/intelligence/runs/latest-dashboard-capable",
        { method: "GET" },
        {
          ...baseDeps,
          getAccessToken: () => "tok",
          reacquireOnce,
          onForbidden,
          fetchImpl: fetchImpl as unknown as typeof fetch,
        },
      ),
    ).rejects.toBeInstanceOf(ApiClientError);
    expect(onForbidden).toHaveBeenCalledTimes(1);
    expect(reacquireOnce).not.toHaveBeenCalled();
  });

  it("does not silently replay when aborted during reacquisition", async () => {
    const controller = new AbortController();
    const reacquireOnce = vi.fn(async () => {
      controller.abort();
      return true;
    });
    const fetchImpl = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            code: "auth.expired",
            message: "expired",
            request_id: "r1",
          }),
          { status: 401 },
        ),
    );
    await expect(
      productFetch(
        "/api/v1/intelligence/runs/latest-dashboard-capable",
        { method: "GET", signal: controller.signal },
        {
          ...baseDeps,
          getAccessToken: () => "old",
          reacquireOnce,
          fetchImpl: fetchImpl as unknown as typeof fetch,
        },
      ),
    ).rejects.toMatchObject({ name: "AbortError" });
    expect(reacquireOnce).toHaveBeenCalledTimes(1);
    expect(fetchImpl).toHaveBeenCalledTimes(1);
  });
});
