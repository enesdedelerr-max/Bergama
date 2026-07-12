"use client";

import { useQuery } from "@tanstack/react-query";
import type { ConsoleScenario } from "@/contracts/types/platform-health";
import { fetchPlatformOverview } from "@/lib/api/platform-health";

export const platformOverviewQueryKey = (scenario: ConsoleScenario) =>
  ["platform-overview", scenario] as const;

export function usePlatformOverview(scenario: ConsoleScenario = "ok") {
  return useQuery({
    queryKey: platformOverviewQueryKey(scenario),
    queryFn: ({ signal }) => fetchPlatformOverview({ scenario, signal }),
    staleTime: 30_000,
    retry: false,
  });
}
