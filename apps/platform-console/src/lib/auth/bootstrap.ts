import type { BootstrapTokenResponse } from "@/contracts/types/product-api";
import { resolveApiBaseUrl } from "@/lib/api/api-base";
import {
  ApiClientError,
  parseProductErrorResponse,
} from "@/lib/api/errors";

export const BOOTSTRAP_PATH = "/api/v1/auth/token" as const;
export const BOOTSTRAP_BODY = { grant_type: "bootstrap" } as const;
export const BOOTSTRAP_DISABLED_CODE = "auth.bootstrap_disabled" as const;

export type BootstrapFetch = typeof fetch;

export async function requestBootstrapToken(options: {
  fetchImpl?: BootstrapFetch;
  signal?: AbortSignal;
  apiBaseUrl?: string;
}): Promise<BootstrapTokenResponse> {
  const base = options.apiBaseUrl ?? resolveApiBaseUrl();
  const fetchImpl = options.fetchImpl ?? fetch;
  const response = await fetchImpl(`${base}${BOOTSTRAP_PATH}`, {
    method: "POST",
    credentials: "omit",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(BOOTSTRAP_BODY),
    signal: options.signal,
  });

  if (!response.ok) {
    const error = await parseProductErrorResponse(response);
    throw error;
  }

  const payload = (await response.json()) as BootstrapTokenResponse;
  if (
    typeof payload.access_token !== "string" ||
    payload.access_token.length === 0 ||
    payload.token_type !== "bearer" ||
    typeof payload.expires_in !== "number" ||
    payload.expires_in <= 0
  ) {
    throw new ApiClientError(
      "auth.bootstrap_invalid_response",
      "Bootstrap token response is invalid",
      500,
    );
  }

  return payload;
}

/** Decode JWT payload claims without verifying signature (server already issued). */
export function readJwtScopes(accessToken: string): string[] {
  const parts = accessToken.split(".");
  if (parts.length < 2) {
    return [];
  }
  try {
    const normalized = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(
      normalized.length + ((4 - (normalized.length % 4)) % 4),
      "=",
    );
    const json =
      typeof atob === "function"
        ? atob(padded)
        : Buffer.from(padded, "base64").toString("utf8");
    const claims = JSON.parse(json) as { scopes?: unknown };
    if (!Array.isArray(claims.scopes)) {
      return [];
    }
    return claims.scopes.filter((scope): scope is string => typeof scope === "string");
  } catch {
    return [];
  }
}
