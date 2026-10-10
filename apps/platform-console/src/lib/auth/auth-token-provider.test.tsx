import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { intelligenceRunQueryKeys } from "@/lib/api/query-keys";
import { productFetch } from "@/lib/api/product-fetch";
import {
  AuthTokenProvider,
  useAuthToken,
  type AuthTokenContextValue,
} from "@/lib/auth/auth-token-provider";
import { AUTH_STATES, PRODUCT_READ_SCOPE } from "@/lib/auth/states";
import { MemoryTokenStore } from "@/lib/auth/memory-token-store";
import { SessionProvider, useSession } from "@/components/providers/session-provider";
import {
  BOOTSTRAP_BODY,
  BOOTSTRAP_DISABLED_CODE,
  BOOTSTRAP_PATH,
} from "@/lib/auth/bootstrap";

function encodeJwt(scopes: string[], jti = "default"): string {
  const header = Buffer.from(
    JSON.stringify({ alg: "none", typ: "JWT" }),
  ).toString("base64url");
  const payload = Buffer.from(JSON.stringify({ scopes, jti })).toString(
    "base64url",
  );
  return `${header}.${payload}.sig`;
}

function Probe({
  onReady,
}: {
  onReady: (api: ReturnType<typeof useAuthToken>) => void;
}) {
  const api = useAuthToken();
  onReady(api);
  return <div data-testid="auth-state">{api.state}</div>;
}

function SessionProbe({
  onReady,
}: {
  onReady: (session: ReturnType<typeof useSession>) => void;
}) {
  const session = useSession();
  onReady(session);
  return null;
}

function renderAuth(
  fetchImpl: typeof fetch,
  onReady: (api: ReturnType<typeof useAuthToken>) => void,
  queryClient = new QueryClient(),
) {
  return render(
    <QueryClientProvider client={queryClient}>
      <SessionProvider>
        <AuthTokenProvider
          fetchImpl={fetchImpl}
          apiBaseUrl="http://localhost:8000"
        >
          <Probe onReady={onReady} />
          <SessionProbe onReady={() => undefined} />
        </AuthTokenProvider>
      </SessionProvider>
    </QueryClientProvider>,
  );
}

describe("AuthTokenProvider", () => {
  it("exposes exactly seven auth states and keeps SessionProvider separate", async () => {
    expect(AUTH_STATES).toEqual([
      "UNAUTHENTICATED",
      "BOOTSTRAP_LOADING",
      "AUTHENTICATED",
      "EXPIRED",
      "BOOTSTRAP_DISABLED",
      "BOOTSTRAP_FAILED",
      "INSUFFICIENT_SCOPE",
    ]);
    const holder: {
      auth: AuthTokenContextValue | null;
      session: ReturnType<typeof useSession> | null;
    } = { auth: null, session: null };
    const fetchImpl = vi.fn();
    render(
      <QueryClientProvider client={new QueryClient()}>
        <SessionProvider>
          <AuthTokenProvider
            fetchImpl={fetchImpl as unknown as typeof fetch}
            apiBaseUrl="http://localhost:8000"
          >
            <Probe
              onReady={(api) => {
                holder.auth = api;
              }}
            />
            <SessionProbe
              onReady={(session) => {
                holder.session = session;
              }}
            />
          </AuthTokenProvider>
        </SessionProvider>
      </QueryClientProvider>,
    );
    await waitFor(() => {
      expect(holder.auth?.state).toBe("UNAUTHENTICATED");
      expect(holder.session?.session?.authenticated).toBe(true);
    });
    expect(holder.auth?.getAccessToken()).toBeNull();
    expect(fetchImpl).not.toHaveBeenCalled();
    expect(
      typeof (holder.session as { getAccessToken?: unknown } | null)
        ?.getAccessToken,
    ).toBe("undefined");
  });

  it("bootstraps with exact body and requires intelligence:runs:read", async () => {
    let authApi: ReturnType<typeof useAuthToken> | null = null;
    const fetchImpl = vi.fn(async (_url, init) => {
      expect(JSON.parse(String(init?.body))).toEqual(BOOTSTRAP_BODY);
      expect(String(_url)).toContain(BOOTSTRAP_PATH);
      return new Response(
        JSON.stringify({
          access_token: encodeJwt([PRODUCT_READ_SCOPE, "api:read"]),
          token_type: "bearer",
          expires_in: 900,
        }),
        { status: 200 },
      );
    });
    renderAuth(fetchImpl as unknown as typeof fetch, (api) => {
      authApi = api;
    });
    await waitFor(() => expect(authApi).not.toBeNull());
    const ok = await authApi!.acquireBootstrap();
    expect(ok).toBe(true);
    await waitFor(() => expect(authApi!.state).toBe("AUTHENTICATED"));
    expect(authApi!.getAccessToken()).toBeTruthy();
  });

  it("rejects api:read alone as insufficient scope", async () => {
    let authApi: ReturnType<typeof useAuthToken> | null = null;
    const fetchImpl = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            access_token: encodeJwt(["api:read"]),
            token_type: "bearer",
            expires_in: 900,
          }),
          { status: 200 },
        ),
    );
    renderAuth(fetchImpl as unknown as typeof fetch, (api) => {
      authApi = api;
    });
    await waitFor(() => expect(authApi).not.toBeNull());
    await authApi!.acquireBootstrap();
    await waitFor(() => expect(authApi!.state).toBe("INSUFFICIENT_SCOPE"));
    expect(authApi!.getAccessToken()).toBeNull();
  });

  it("maps bootstrap disabled and failure", async () => {
    let authApi: ReturnType<typeof useAuthToken> | null = null;
    const disabledFetch = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            code: BOOTSTRAP_DISABLED_CODE,
            message: "disabled",
            request_id: "r1",
          }),
          { status: 404 },
        ),
    );
    renderAuth(disabledFetch as unknown as typeof fetch, (api) => {
      authApi = api;
    });
    await waitFor(() => expect(authApi).not.toBeNull());
    await authApi!.acquireBootstrap();
    await waitFor(() => expect(authApi!.state).toBe("BOOTSTRAP_DISABLED"));

    const failedFetch = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            code: "auth.bootstrap_failed",
            message: "failed",
            request_id: "r2",
          }),
          { status: 500 },
        ),
    );
    let authApi2: ReturnType<typeof useAuthToken> | null = null;
    renderAuth(failedFetch as unknown as typeof fetch, (api) => {
      authApi2 = api;
    });
    await waitFor(() => expect(authApi2).not.toBeNull());
    await authApi2!.acquireBootstrap();
    await waitFor(() => expect(authApi2!.state).toBe("BOOTSTRAP_FAILED"));
  });

  it("expires token into EXPIRED and clears cache", async () => {
    let nowMs = 1_000_000;
    let authApi: ReturnType<typeof useAuthToken> | null = null;
    const queryClient = new QueryClient();
    queryClient.setQueryData(intelligenceRunQueryKeys.latestDashboardCapable, {
      ok: true,
    });
    const fetchImpl = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            access_token: encodeJwt([PRODUCT_READ_SCOPE]),
            token_type: "bearer",
            expires_in: 1,
          }),
          { status: 200 },
        ),
    );
    render(
      <QueryClientProvider client={queryClient}>
        <AuthTokenProvider
          fetchImpl={fetchImpl as unknown as typeof fetch}
          apiBaseUrl="http://localhost:8000"
          now={() => nowMs}
        >
          <Probe
            onReady={(api) => {
              authApi = api;
            }}
          />
        </AuthTokenProvider>
      </QueryClientProvider>,
    );
    await waitFor(() => expect(authApi).not.toBeNull());
    await authApi!.acquireBootstrap();
    await waitFor(() => expect(authApi!.state).toBe("AUTHENTICATED"));
    nowMs = 1_000_000 + 2_000;
    expect(authApi!.getAccessToken()).toBeNull();
    await waitFor(() => expect(authApi!.state).toBe("EXPIRED"));
    expect(
      queryClient.getQueryData(intelligenceRunQueryKeys.latestDashboardCapable),
    ).toBeUndefined();
  });

  it("reacquireOnce clears token/cache and shares one flight for same generation", async () => {
    let authApi: ReturnType<typeof useAuthToken> | null = null;
    const queryClient = new QueryClient();
    queryClient.setQueryData(intelligenceRunQueryKeys.byId("r"), { x: 1 });
    let bootstrapCalls = 0;
    const fetchImpl = vi.fn(async () => {
      bootstrapCalls += 1;
      return new Response(
        JSON.stringify({
          access_token: encodeJwt([PRODUCT_READ_SCOPE]),
          token_type: "bearer",
          expires_in: 900,
        }),
        { status: 200 },
      );
    });
    render(
      <QueryClientProvider client={queryClient}>
        <AuthTokenProvider
          fetchImpl={fetchImpl as unknown as typeof fetch}
          apiBaseUrl="http://localhost:8000"
        >
          <Probe
            onReady={(api) => {
              authApi = api;
            }}
          />
        </AuthTokenProvider>
      </QueryClientProvider>,
    );
    await waitFor(() => expect(authApi).not.toBeNull());
    await authApi!.acquireBootstrap();
    expect(bootstrapCalls).toBe(1);
    const staleGeneration = authApi!.getAuthGeneration();
    queryClient.setQueryData(intelligenceRunQueryKeys.byId("r"), { x: 1 });
    const first = await authApi!.reacquireOnce(staleGeneration);
    expect(first).toBe(true);
    expect(bootstrapCalls).toBe(2);
    expect(queryClient.getQueryData(intelligenceRunQueryKeys.byId("r"))).toBeUndefined();

    const failFetch = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            code: "auth.bootstrap_failed",
            message: "fail",
            request_id: "r",
          }),
          { status: 500 },
        ),
    );
    let authApiFail: ReturnType<typeof useAuthToken> | null = null;
    render(
      <QueryClientProvider client={new QueryClient()}>
        <AuthTokenProvider
          fetchImpl={failFetch as unknown as typeof fetch}
          apiBaseUrl="http://localhost:8000"
        >
          <Probe
            onReady={(api) => {
              authApiFail = api;
            }}
          />
        </AuthTokenProvider>
      </QueryClientProvider>,
    );
    await waitFor(() => expect(authApiFail).not.toBeNull());
    const gen = authApiFail!.getAuthGeneration();
    const a = await authApiFail!.reacquireOnce(gen);
    const b = await authApiFail!.reacquireOnce(gen);
    expect(a).toBe(false);
    expect(b).toBe(false);
    expect(failFetch).toHaveBeenCalledTimes(1);
  });

  it("concurrent dual 401 shares one bootstrap and late sibling cannot clear fresh token", async () => {
    let authApi: ReturnType<typeof useAuthToken> | null = null;
    let resolveBootstrap: ((value: Response) => void) | null = null;
    let bootstrapCalls = 0;
    let productMode: "unauthorized" | "ok" = "unauthorized";
    const initialToken = encodeJwt([PRODUCT_READ_SCOPE], "initial");
    const freshToken = encodeJwt([PRODUCT_READ_SCOPE], "recovered");
    const fetchImpl = vi.fn(async (url: string) => {
      if (String(url).includes(BOOTSTRAP_PATH)) {
        bootstrapCalls += 1;
        if (bootstrapCalls === 1) {
          return new Response(
            JSON.stringify({
              access_token: initialToken,
              token_type: "bearer",
              expires_in: 900,
            }),
            { status: 200 },
          );
        }
        if (bootstrapCalls === 2) {
          return await new Promise<Response>((resolve) => {
            resolveBootstrap = resolve;
          });
        }
        throw new Error("unexpected extra bootstrap");
      }
      if (productMode === "unauthorized") {
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

    render(
      <QueryClientProvider client={new QueryClient()}>
        <AuthTokenProvider
          fetchImpl={fetchImpl as unknown as typeof fetch}
          apiBaseUrl="http://localhost:8000"
        >
          <Probe
            onReady={(api) => {
              authApi = api;
            }}
          />
        </AuthTokenProvider>
      </QueryClientProvider>,
    );
    await waitFor(() => expect(authApi).not.toBeNull());
    await authApi!.acquireBootstrap();
    await waitFor(() => expect(authApi!.state).toBe("AUTHENTICATED"));
    const staleGeneration = authApi!.getAuthGeneration();
    const oldToken = authApi!.getAccessToken();
    expect(oldToken).toBeTruthy();

    const deps = {
      getAccessToken: () => authApi!.getAccessToken(),
      getAuthGeneration: () => staleGeneration,
      reacquireOnce: (requestGeneration: number) =>
        authApi!.reacquireOnce(requestGeneration),
      onForbidden: () => undefined,
      fetchImpl: fetchImpl as unknown as typeof fetch,
      apiBaseUrl: "http://localhost:8000",
    };

    const path = "/api/v1/intelligence/runs/latest-dashboard-capable";
    const p1 = productFetch(path, { method: "GET" }, deps);
    const p2 = productFetch(path, { method: "GET" }, deps);

    await waitFor(() => expect(bootstrapCalls).toBe(2));
    expect(resolveBootstrap).not.toBeNull();

    // Arm successful product responses before completing recovery replay.
    productMode = "ok";
    resolveBootstrap!(
      new Response(
        JSON.stringify({
          access_token: freshToken,
          token_type: "bearer",
          expires_in: 900,
        }),
        { status: 200 },
      ),
    );

    const [r1, r2] = await Promise.all([p1, p2]);
    expect(r1.status).toBe(200);
    expect(r2.status).toBe(200);
    expect(bootstrapCalls).toBe(2);
    await waitFor(() => {
      expect(authApi!.state).toBe("AUTHENTICATED");
      expect(authApi!.getAccessToken()).toBe(freshToken);
    });
    expect(authApi!.getAccessToken()).not.toBe(oldToken);

    const late = await authApi!.reacquireOnce(staleGeneration);
    expect(late).toBe(true);
    expect(bootstrapCalls).toBe(2);
    expect(authApi!.getAccessToken()).toBe(freshToken);
    await waitFor(() => expect(authApi!.state).toBe("AUTHENTICATED"));
  });

  it("logout during in-flight bootstrap discards stale token completion", async () => {
    let authApi: ReturnType<typeof useAuthToken> | null = null;
    let resolveBootstrap: ((value: Response) => void) | null = null;
    const fetchImpl = vi.fn(
      async () =>
        await new Promise<Response>((resolve) => {
          resolveBootstrap = resolve;
        }),
    );
    renderAuth(fetchImpl as unknown as typeof fetch, (api) => {
      authApi = api;
    });
    await waitFor(() => expect(authApi).not.toBeNull());

    const acquirePromise = authApi!.acquireBootstrap();
    await waitFor(() => expect(resolveBootstrap).not.toBeNull());
    authApi!.logout();
    await waitFor(() => expect(authApi!.state).toBe("UNAUTHENTICATED"));

    resolveBootstrap!(
      new Response(
        JSON.stringify({
          access_token: encodeJwt([PRODUCT_READ_SCOPE]),
          token_type: "bearer",
          expires_in: 900,
        }),
        { status: 200 },
      ),
    );

    const ok = await acquirePromise;
    expect(ok).toBe(false);
    expect(authApi!.getAccessToken()).toBeNull();
    await waitFor(() => expect(authApi!.state).toBe("UNAUTHENTICATED"));
  });

  it("late stale 401 after successful recovery does not clear fresh token", async () => {
    let authApi: ReturnType<typeof useAuthToken> | null = null;
    const fetchImpl = vi.fn(async () => {
      return new Response(
        JSON.stringify({
          access_token: encodeJwt([PRODUCT_READ_SCOPE]),
          token_type: "bearer",
          expires_in: 900,
        }),
        { status: 200 },
      );
    });
    renderAuth(fetchImpl as unknown as typeof fetch, (api) => {
      authApi = api;
    });
    await waitFor(() => expect(authApi).not.toBeNull());
    await authApi!.acquireBootstrap();
    await waitFor(() => expect(authApi!.state).toBe("AUTHENTICATED"));
    const generationG = authApi!.getAuthGeneration();
    const recovered = await authApi!.reacquireOnce(generationG);
    expect(recovered).toBe(true);
    await waitFor(() => expect(authApi!.state).toBe("AUTHENTICATED"));
    const fresh = authApi!.getAccessToken();
    expect(fresh).toBeTruthy();
    const generationAfter = authApi!.getAuthGeneration();
    expect(generationAfter).toBeGreaterThan(generationG);

    const late = await authApi!.reacquireOnce(generationG);
    expect(late).toBe(true);
    expect(authApi!.getAccessToken()).toBe(fresh);
    expect(authApi!.getAuthGeneration()).toBe(generationAfter);
    await waitFor(() => expect(authApi!.state).toBe("AUTHENTICATED"));
    // Only initial + one recovery bootstrap.
    expect(fetchImpl).toHaveBeenCalledTimes(2);
  });

  it("markInsufficientScope retains token semantics for 403 path", async () => {
    let authApi: ReturnType<typeof useAuthToken> | null = null;
    const fetchImpl = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            access_token: encodeJwt([PRODUCT_READ_SCOPE]),
            token_type: "bearer",
            expires_in: 900,
          }),
          { status: 200 },
        ),
    );
    renderAuth(fetchImpl as unknown as typeof fetch, (api) => {
      authApi = api;
    });
    await waitFor(() => expect(authApi).not.toBeNull());
    await authApi!.acquireBootstrap();
    const token = authApi!.getAccessToken();
    expect(token).toBeTruthy();
    authApi!.markInsufficientScope();
    await waitFor(() => expect(authApi!.state).toBe("INSUFFICIENT_SCOPE"));
    expect(authApi!.getAccessToken()).toBe(token);
  });

  it("memory store does not use web storage APIs", () => {
    const setItem = vi.spyOn(Storage.prototype, "setItem");
    const store = new MemoryTokenStore();
    store.set({
      accessToken: "abc",
      expiresAtMs: Date.now() + 1000,
      scopes: [PRODUCT_READ_SCOPE],
    });
    expect(store.get()?.accessToken).toBe("abc");
    store.clear();
    expect(store.get()).toBeNull();
    expect(setItem).not.toHaveBeenCalled();
    setItem.mockRestore();
  });
});
