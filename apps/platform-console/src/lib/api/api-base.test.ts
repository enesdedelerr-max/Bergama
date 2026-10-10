import { afterEach, describe, expect, it } from "vitest";
import { ApiBaseUrlError, resolveApiBaseUrl } from "@/lib/api/api-base";

const ENV_KEY = "NEXT_PUBLIC_BERGAMA_API_BASE_URL";

describe("resolveApiBaseUrl", () => {
  afterEach(() => {
    delete process.env[ENV_KEY];
  });

  it("accepts a valid absolute origin", () => {
    expect(resolveApiBaseUrl("https://api.example.com")).toBe(
      "https://api.example.com",
    );
  });

  it("strips a trailing slash", () => {
    expect(resolveApiBaseUrl("https://api.example.com/")).toBe(
      "https://api.example.com",
    );
  });

  it("rejects path", () => {
    expect(() => resolveApiBaseUrl("https://api.example.com/v1")).toThrow(
      ApiBaseUrlError,
    );
  });

  it("rejects query", () => {
    expect(() => resolveApiBaseUrl("https://api.example.com?x=1")).toThrow(
      ApiBaseUrlError,
    );
  });

  it("rejects fragment", () => {
    expect(() => resolveApiBaseUrl("https://api.example.com#frag")).toThrow(
      ApiBaseUrlError,
    );
  });

  it("fails closed when missing", () => {
    expect(() => resolveApiBaseUrl(undefined)).toThrow(ApiBaseUrlError);
    expect(() => resolveApiBaseUrl("")).toThrow(ApiBaseUrlError);
  });

  it("allows localhost HTTP", () => {
    expect(resolveApiBaseUrl("http://localhost:8000")).toBe(
      "http://localhost:8000",
    );
  });

  it("allows 127.0.0.1 HTTP", () => {
    expect(resolveApiBaseUrl("http://127.0.0.1:8000")).toBe(
      "http://127.0.0.1:8000",
    );
  });

  it("rejects non-local HTTP", () => {
    expect(() => resolveApiBaseUrl("http://api.example.com")).toThrow(
      ApiBaseUrlError,
    );
  });

  it("rejects userinfo", () => {
    expect(() => resolveApiBaseUrl("https://user:pass@api.example.com")).toThrow(
      ApiBaseUrlError,
    );
  });
});
