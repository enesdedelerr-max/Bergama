export const API_BASE_URL_ENV_KEY = "NEXT_PUBLIC_BERGAMA_API_BASE_URL" as const;

export class ApiBaseUrlError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "ApiBaseUrlError";
    this.code = code;
  }
}

const LOCAL_HTTP_HOSTS = new Set(["localhost", "127.0.0.1"]);

/**
 * Validate and normalize NEXT_PUBLIC_BERGAMA_API_BASE_URL.
 * Fail closed: no same-origin or hard-coded fallback.
 */
export function resolveApiBaseUrl(
  raw: string | undefined | null = process.env.NEXT_PUBLIC_BERGAMA_API_BASE_URL,
): string {
  if (raw === undefined || raw === null || raw.trim() === "") {
    throw new ApiBaseUrlError(
      "api_base.missing",
      `${API_BASE_URL_ENV_KEY} is required`,
    );
  }

  const trimmed = raw.trim();
  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    throw new ApiBaseUrlError(
      "api_base.invalid",
      `${API_BASE_URL_ENV_KEY} must be an absolute URL`,
    );
  }

  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new ApiBaseUrlError(
      "api_base.invalid_scheme",
      `${API_BASE_URL_ENV_KEY} must use http or https`,
    );
  }

  if (parsed.username !== "" || parsed.password !== "") {
    throw new ApiBaseUrlError(
      "api_base.userinfo_forbidden",
      `${API_BASE_URL_ENV_KEY} must not include userinfo`,
    );
  }

  if (parsed.pathname !== "/" && parsed.pathname !== "") {
    throw new ApiBaseUrlError(
      "api_base.path_forbidden",
      `${API_BASE_URL_ENV_KEY} must not include a path`,
    );
  }

  if (parsed.search !== "") {
    throw new ApiBaseUrlError(
      "api_base.query_forbidden",
      `${API_BASE_URL_ENV_KEY} must not include a query`,
    );
  }

  if (parsed.hash !== "") {
    throw new ApiBaseUrlError(
      "api_base.fragment_forbidden",
      `${API_BASE_URL_ENV_KEY} must not include a fragment`,
    );
  }

  const hostname = parsed.hostname.toLowerCase();
  if (!hostname) {
    throw new ApiBaseUrlError(
      "api_base.host_required",
      `${API_BASE_URL_ENV_KEY} must include a host`,
    );
  }

  const isLocalHttpHost = LOCAL_HTTP_HOSTS.has(hostname);
  if (parsed.protocol === "http:" && !isLocalHttpHost) {
    throw new ApiBaseUrlError(
      "api_base.https_required",
      `${API_BASE_URL_ENV_KEY} requires HTTPS outside localhost/127.0.0.1`,
    );
  }

  const port = parsed.port ? `:${parsed.port}` : "";
  return `${parsed.protocol}//${hostname}${port}`;
}
