"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { createIntelligenceClient } from "@/lib/api/intelligence-client";
import { intelligenceRunQueryKeys } from "@/lib/api/query-keys";
import { useAuthToken } from "@/lib/auth/auth-token-provider";

/**
 * Thin Premarket query hooks composing WS1 intelligence client + query keys.
 * Relies on QueryProvider defaults (staleTime/gcTime/retry/refetch/polling).
 * Never embeds bearer tokens in query keys.
 */

function useProductIntelligenceClient() {
  const auth = useAuthToken();
  return useMemo(
    () =>
      createIntelligenceClient({
        getAccessToken: auth.getAccessToken,
        getAuthGeneration: auth.getAuthGeneration,
        reacquireOnce: auth.reacquireOnce,
        onForbidden: auth.markInsufficientScope,
      }),
    [
      auth.getAccessToken,
      auth.getAuthGeneration,
      auth.markInsufficientScope,
      auth.reacquireOnce,
    ],
  );
}

export function useLatestDashboardCapable(enabled: boolean) {
  const client = useProductIntelligenceClient();
  return useQuery({
    queryKey: intelligenceRunQueryKeys.latestDashboardCapable,
    queryFn: ({ signal }) => client.getLatestDashboardCapable(signal),
    enabled,
  });
}

export function useIntelligenceRunById(runId: string, enabled: boolean) {
  const client = useProductIntelligenceClient();
  return useQuery({
    queryKey: intelligenceRunQueryKeys.byId(runId),
    queryFn: ({ signal }) => client.getRunById(runId, signal),
    enabled: enabled && runId.length > 0,
  });
}

export function useIntelligenceRunByFingerprint(
  fingerprint: string | null,
  enabled: boolean,
) {
  const client = useProductIntelligenceClient();
  const key = fingerprint ?? "";
  return useQuery({
    queryKey: intelligenceRunQueryKeys.byFingerprint(key),
    queryFn: ({ signal }) => {
      if (!fingerprint) {
        throw new Error("fingerprint required");
      }
      return client.getRunByFingerprint(fingerprint, signal);
    },
    enabled: enabled && Boolean(fingerprint),
  });
}

export function useRunDashboard(runId: string, enabled: boolean) {
  const client = useProductIntelligenceClient();
  return useQuery({
    queryKey: intelligenceRunQueryKeys.dashboard(runId),
    queryFn: ({ signal }) => client.getRunDashboard(runId, signal),
    enabled: enabled && runId.length > 0,
  });
}

export function useRunHumanReview(runId: string, enabled: boolean) {
  const client = useProductIntelligenceClient();
  return useQuery({
    queryKey: intelligenceRunQueryKeys.humanReview(runId),
    queryFn: ({ signal }) => client.getRunHumanReview(runId, signal),
    enabled: enabled && runId.length > 0,
  });
}

export function useRunAde(runId: string, enabled: boolean) {
  const client = useProductIntelligenceClient();
  return useQuery({
    queryKey: intelligenceRunQueryKeys.ade(runId),
    queryFn: ({ signal }) => client.getRunAde(runId, signal),
    enabled: enabled && runId.length > 0,
  });
}
