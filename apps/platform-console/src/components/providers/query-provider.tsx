"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { ApiClientError, isAbortError } from "@/lib/api/errors";

export const QUERY_STALE_TIME_MS = 30_000;
export const QUERY_GC_TIME_MS = 300_000;

export function createPlatformQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: QUERY_STALE_TIME_MS,
        gcTime: QUERY_GC_TIME_MS,
        refetchOnWindowFocus: false,
        refetchOnReconnect: false,
        refetchInterval: false,
        retry: (failureCount, error) => {
          if (isAbortError(error)) {
            return false;
          }
          if (error instanceof ApiClientError) {
            if (error.status === 401) {
              // 401 is owned exclusively by auth reacquisition, not TanStack retry.
              return false;
            }
            if (error.status === 503) {
              return failureCount < 1;
            }
            if (error.status >= 400 && error.status < 500) {
              return false;
            }
            if (error.status >= 500) {
              return false;
            }
          }
          // Network / unknown transport failures: at most one retry.
          return failureCount < 1;
        },
      },
    },
  });
}

export function QueryProvider({ children }: { children: ReactNode }) {
  const [client] = useState(() => createPlatformQueryClient());

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
