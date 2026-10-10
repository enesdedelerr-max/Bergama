import type { QueryClient } from "@tanstack/react-query";
import { intelligenceRunQueryKeys } from "@/lib/api/query-keys";

/** Clear Premarket / product intelligence query cache (logout, replace, 401, expiry). */
export function clearProductQueryCache(queryClient: QueryClient): void {
  void queryClient.removeQueries({ queryKey: intelligenceRunQueryKeys.all });
}
