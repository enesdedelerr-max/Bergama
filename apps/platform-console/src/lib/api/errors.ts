import type { ProductErrorResponse } from "@/contracts/types/product-api";

export class ApiClientError extends Error {
  readonly code: string;
  readonly status: number;
  readonly requestId: string | null;
  readonly details: Record<string, unknown> | null;

  constructor(
    code: string,
    message: string,
    status: number,
    requestId: string | null = null,
    details: Record<string, unknown> | null = null,
  ) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.status = status;
    this.requestId = requestId;
    this.details = details;
  }
}

export function isUnauthorizedError(error: unknown): boolean {
  return error instanceof ApiClientError && error.status === 401;
}

export function isForbiddenError(error: unknown): boolean {
  return error instanceof ApiClientError && error.status === 403;
}

export function isAbortError(error: unknown): boolean {
  return (
    (error instanceof DOMException && error.name === "AbortError") ||
    (error instanceof Error && error.name === "AbortError")
  );
}

export async function parseProductErrorResponse(
  response: Response,
): Promise<ApiClientError> {
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    return new ApiClientError(
      "product_error.unparseable",
      response.statusText || "Product API error",
      response.status,
    );
  }

  if (!isProductErrorResponse(body)) {
    return new ApiClientError(
      "product_error.invalid_shape",
      response.statusText || "Product API error",
      response.status,
    );
  }

  return new ApiClientError(
    body.code,
    body.message,
    response.status,
    body.request_id,
    body.details ?? null,
  );
}

export function isProductErrorResponse(value: unknown): value is ProductErrorResponse {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const record = value as Record<string, unknown>;
  return (
    typeof record.code === "string" &&
    record.code.length > 0 &&
    typeof record.message === "string" &&
    record.message.length > 0 &&
    typeof record.request_id === "string" &&
    record.request_id.length > 0 &&
    (record.details === undefined ||
      record.details === null ||
      (typeof record.details === "object" && !Array.isArray(record.details)))
  );
}
