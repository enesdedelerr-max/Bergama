"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import { clearProductQueryCache } from "@/lib/api/product-cache";
import { ApiClientError } from "@/lib/api/errors";
import {
  BOOTSTRAP_DISABLED_CODE,
  readJwtScopes,
  requestBootstrapToken,
} from "@/lib/auth/bootstrap";
import { MemoryTokenStore } from "@/lib/auth/memory-token-store";
import {
  AUTH_STATES,
  PRODUCT_READ_SCOPE,
  type AuthState,
} from "@/lib/auth/states";

export type AuthTokenContextValue = {
  state: AuthState;
  scopes: readonly string[];
  getAccessToken: () => string | null;
  /** Memory-only auth lifecycle generation (not for query keys / product data). */
  getAuthGeneration: () => number;
  /** Explicit authorized bootstrap acquire for local/dev/test. */
  acquireBootstrap: () => Promise<boolean>;
  /**
   * Sole owner of 401 reacquisition for a request's auth generation.
   * Concurrent callers for the same generation share one recovery flight.
   */
  reacquireOnce: (requestGeneration: number) => Promise<boolean>;
  markInsufficientScope: () => void;
  logout: () => void;
  authStates: typeof AUTH_STATES;
};

const AuthTokenContext = createContext<AuthTokenContextValue | null>(null);

export type AuthTokenProviderProps = {
  children: ReactNode;
  fetchImpl?: typeof fetch;
  apiBaseUrl?: string;
  now?: () => number;
};

type RecoveryFlight = {
  forGeneration: number;
  promise: Promise<boolean>;
};

export function AuthTokenProvider({
  children,
  fetchImpl,
  apiBaseUrl,
  now = () => Date.now(),
}: AuthTokenProviderProps) {
  const queryClient = useQueryClient();
  const storeRef = useRef(new MemoryTokenStore());
  const [state, setState] = useState<AuthState>("UNAUTHENTICATED");
  const [scopes, setScopes] = useState<readonly string[]>([]);
  const expiryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  /** Monotonic auth lifecycle generation (memory only). */
  const authGenerationRef = useRef(0);
  /** Generation of the currently installed token, if any. */
  const tokenGenerationRef = useRef<number | null>(null);
  /** Single-flight recovery keyed by the stale request generation. */
  const recoveryFlightRef = useRef<RecoveryFlight | null>(null);
  /** Explicit bootstrap in-flight (also generation-guarded). */
  const explicitAcquireRef = useRef<Promise<boolean> | null>(null);

  const getAuthGeneration = useCallback(() => authGenerationRef.current, []);

  const advanceGeneration = useCallback(() => {
    authGenerationRef.current += 1;
  }, []);

  const clearExpiryTimer = useCallback(() => {
    if (expiryTimerRef.current !== null) {
      clearTimeout(expiryTimerRef.current);
      expiryTimerRef.current = null;
    }
  }, []);

  const clearProductAuth = useCallback(
    (nextState: AuthState) => {
      advanceGeneration();
      clearExpiryTimer();
      storeRef.current.clear();
      tokenGenerationRef.current = null;
      setScopes([]);
      clearProductQueryCache(queryClient);
      setState(nextState);
    },
    [advanceGeneration, clearExpiryTimer, queryClient],
  );

  const scheduleExpiry = useCallback(
    (expiresAtMs: number, tokenGeneration: number) => {
      clearExpiryTimer();
      const delay = Math.max(0, expiresAtMs - now());
      expiryTimerRef.current = setTimeout(() => {
        // Do not clear a newer token generation.
        if (tokenGenerationRef.current !== tokenGeneration) {
          return;
        }
        if (authGenerationRef.current !== tokenGeneration) {
          return;
        }
        clearProductAuth("EXPIRED");
      }, delay);
    },
    [clearExpiryTimer, clearProductAuth, now],
  );

  const applyToken = useCallback(
    (accessToken: string, expiresInSeconds: number, expectedGeneration: number) => {
      if (authGenerationRef.current !== expectedGeneration) {
        return false;
      }
      const tokenScopes = readJwtScopes(accessToken);
      if (!tokenScopes.includes(PRODUCT_READ_SCOPE)) {
        clearProductAuth("INSUFFICIENT_SCOPE");
        return false;
      }
      // Successful install opens a new authenticated lifecycle generation.
      advanceGeneration();
      const tokenGeneration = authGenerationRef.current;
      const expiresAtMs = now() + expiresInSeconds * 1000;
      storeRef.current.set({
        accessToken,
        expiresAtMs,
        scopes: tokenScopes,
      });
      tokenGenerationRef.current = tokenGeneration;
      setScopes(tokenScopes);
      setState("AUTHENTICATED");
      scheduleExpiry(expiresAtMs, tokenGeneration);
      clearProductQueryCache(queryClient);
      return true;
    },
    [advanceGeneration, clearProductAuth, now, queryClient, scheduleExpiry],
  );

  const runBootstrapAcquire = useCallback(
    async (expectedGeneration: number): Promise<boolean> => {
      setState("BOOTSTRAP_LOADING");
      try {
        const token = await requestBootstrapToken({
          fetchImpl,
          apiBaseUrl,
        });
        return applyToken(
          token.access_token,
          token.expires_in,
          expectedGeneration,
        );
      } catch (error) {
        if (authGenerationRef.current !== expectedGeneration) {
          return false;
        }
        if (
          error instanceof ApiClientError &&
          error.status === 404 &&
          error.code === BOOTSTRAP_DISABLED_CODE
        ) {
          clearProductAuth("BOOTSTRAP_DISABLED");
          return false;
        }
        clearProductAuth("BOOTSTRAP_FAILED");
        return false;
      }
    },
    [apiBaseUrl, applyToken, clearProductAuth, fetchImpl],
  );

  const acquireBootstrap = useCallback(async () => {
    if (explicitAcquireRef.current) {
      return explicitAcquireRef.current;
    }
    // Explicit acquire invalidates prior async work by advancing generation.
    advanceGeneration();
    storeRef.current.clear();
    tokenGenerationRef.current = null;
    recoveryFlightRef.current = null;
    clearExpiryTimer();
    clearProductQueryCache(queryClient);
    const expectedGeneration = authGenerationRef.current;
    const work = (async () => {
      try {
        return await runBootstrapAcquire(expectedGeneration);
      } finally {
        explicitAcquireRef.current = null;
      }
    })();
    explicitAcquireRef.current = work;
    return work;
  }, [
    advanceGeneration,
    clearExpiryTimer,
    queryClient,
    runBootstrapAcquire,
  ]);

  const reacquireOnce = useCallback(
    async (requestGeneration: number): Promise<boolean> => {
      const hasValidToken = (): boolean => {
        const stored = storeRef.current.get();
        if (!stored) {
          return false;
        }
        if (now() >= stored.expiresAtMs) {
          return false;
        }
        return tokenGenerationRef.current !== null;
      };

      // Join single-flight recovery for this stale generation.
      const existing = recoveryFlightRef.current;
      if (existing && existing.forGeneration === requestGeneration) {
        return existing.promise;
      }

      // Request generation already superseded: do not clear a fresher lifecycle.
      if (requestGeneration < authGenerationRef.current) {
        return hasValidToken();
      }

      // requestGeneration === current: start the only recovery flight for this gen.
      if (requestGeneration !== authGenerationRef.current) {
        return hasValidToken();
      }

      const flight = (async () => {
        // Invalidate the stale authenticated generation (clears token/cache).
        clearProductAuth("UNAUTHENTICATED");
        const expectedGeneration = authGenerationRef.current;
        try {
          return await runBootstrapAcquire(expectedGeneration);
        } finally {
          if (
            recoveryFlightRef.current &&
            recoveryFlightRef.current.forGeneration === requestGeneration
          ) {
            recoveryFlightRef.current = null;
          }
        }
      })();

      recoveryFlightRef.current = {
        forGeneration: requestGeneration,
        promise: flight,
      };
      return flight;
    },
    [clearProductAuth, now, runBootstrapAcquire],
  );

  const getAccessToken = useCallback(() => {
    const stored = storeRef.current.get();
    if (!stored) {
      return null;
    }
    if (now() >= stored.expiresAtMs) {
      const tokenGeneration = tokenGenerationRef.current;
      if (
        tokenGeneration !== null &&
        authGenerationRef.current === tokenGeneration
      ) {
        clearProductAuth("EXPIRED");
      }
      return null;
    }
    return stored.accessToken;
  }, [clearProductAuth, now]);

  const markInsufficientScope = useCallback(() => {
    setState("INSUFFICIENT_SCOPE");
  }, []);

  const logout = useCallback(() => {
    // Advances generation so in-flight bootstrap/reacquire completions are ignored.
    clearProductAuth("UNAUTHENTICATED");
    recoveryFlightRef.current = null;
    explicitAcquireRef.current = null;
  }, [clearProductAuth]);

  useEffect(() => {
    return () => {
      clearExpiryTimer();
    };
  }, [clearExpiryTimer]);

  const value = useMemo<AuthTokenContextValue>(
    () => ({
      state,
      scopes,
      getAccessToken,
      getAuthGeneration,
      acquireBootstrap,
      reacquireOnce,
      markInsufficientScope,
      logout,
      authStates: AUTH_STATES,
    }),
    [
      acquireBootstrap,
      getAccessToken,
      getAuthGeneration,
      logout,
      markInsufficientScope,
      reacquireOnce,
      scopes,
      state,
    ],
  );

  return (
    <AuthTokenContext.Provider value={value}>{children}</AuthTokenContext.Provider>
  );
}

export function useAuthToken(): AuthTokenContextValue {
  const context = useContext(AuthTokenContext);
  if (!context) {
    throw new Error("useAuthToken must be used within AuthTokenProvider");
  }
  return context;
}
