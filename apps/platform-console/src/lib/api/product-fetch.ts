import { resolveApiBaseUrl } from "@/lib/api/api-base";
import {
  ApiClientError,
  parseProductErrorResponse,
} from "@/lib/api/errors";

export type ProductFetchDeps = {
  getAccessToken: () => string | null;
  /** Auth generation captured with the request; used to ignore stale 401s. */
  getAuthGeneration: () => number;
  /**
   * Sole owner of 401 reacquisition for the request's auth generation.
   * Returns true when a usable token exists for a single replay.
   */
  reacquireOnce: (requestGeneration: number) => Promise<boolean>;
  onForbidden: () => void;
  fetchImpl?: typeof fetch;
  apiBaseUrl?: string;
};

type ProductRequestInit = {
  method?: "GET" | "POST";
  body?: string;
  signal?: AbortSignal;
  headers?: Record<string, string>;
  /** Internal: marks a single replay after successful reacquisition. */
  __replayed?: boolean;
};

function abortError(): DOMException {
  return new DOMException("The operation was aborted.", "AbortError");
}

/**
 * Native product fetch: credentials omit, Bearer when authenticated,
 * AbortSignal, bounded 401 reacquisition/replay owned by reacquireOnce.
 */
export async function productFetch(
  path: string,
  init: ProductRequestInit,
  deps: ProductFetchDeps,
): Promise<Response> {
  const base = deps.apiBaseUrl ?? resolveApiBaseUrl();
  const fetchImpl = deps.fetchImpl ?? fetch;
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(init.headers ?? {}),
  };
  const requestGeneration = deps.getAuthGeneration();
  const token = deps.getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetchImpl(`${base}${path}`, {
    method: init.method ?? "GET",
    credentials: "omit",
    headers,
    body: init.body,
    signal: init.signal,
  });

  if (response.status === 401) {
    if (init.__replayed) {
      throw await parseProductErrorResponse(response);
    }
    if (init.signal?.aborted) {
      throw abortError();
    }
    const reacquired = await deps.reacquireOnce(requestGeneration);
    if (!reacquired) {
      throw await parseProductErrorResponse(response);
    }
    if (init.signal?.aborted) {
      throw abortError();
    }
    return productFetch(path, { ...init, __replayed: true }, deps);
  }

  if (response.status === 403) {
    deps.onForbidden();
    throw await parseProductErrorResponse(response);
  }

  return response;
}

export async function readJsonOrThrow<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw await parseProductErrorResponse(response);
  }
  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiClientError(
      "product_response.invalid_json",
      "Product API returned invalid JSON",
      response.status,
    );
  }
}
