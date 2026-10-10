import type {
  IntelligenceRunAdeRead,
  IntelligenceRunDashboardRead,
  IntelligenceRunHumanReviewRead,
  IntelligenceRunRead,
} from "@/contracts/types/product-api";
import {
  productFetch,
  readJsonOrThrow,
  type ProductFetchDeps,
} from "@/lib/api/product-fetch";
import { BOOTSTRAP_PATH, requestBootstrapToken } from "@/lib/auth/bootstrap";

const RUNS_PREFIX = "/api/v1/intelligence/runs";

export type IntelligenceClient = {
  getRunById: (
    runId: string,
    signal?: AbortSignal,
  ) => Promise<IntelligenceRunRead>;
  getRunByFingerprint: (
    fingerprint: string,
    signal?: AbortSignal,
  ) => Promise<IntelligenceRunRead>;
  getLatestDashboardCapable: (
    signal?: AbortSignal,
  ) => Promise<IntelligenceRunRead>;
  getRunDashboard: (
    runId: string,
    signal?: AbortSignal,
  ) => Promise<IntelligenceRunDashboardRead>;
  getRunHumanReview: (
    runId: string,
    signal?: AbortSignal,
  ) => Promise<IntelligenceRunHumanReviewRead>;
  getRunAde: (
    runId: string,
    signal?: AbortSignal,
  ) => Promise<IntelligenceRunAdeRead>;
  /** Authorized bootstrap POST only — not an intelligence write helper. */
  postBootstrapToken: (
    signal?: AbortSignal,
  ) => ReturnType<typeof requestBootstrapToken>;
};

export function createIntelligenceClient(
  deps: ProductFetchDeps,
): IntelligenceClient {
  return {
    async getRunById(runId, signal) {
      const response = await productFetch(
        `${RUNS_PREFIX}/id/${encodeURIComponent(runId)}`,
        { method: "GET", signal },
        deps,
      );
      return readJsonOrThrow<IntelligenceRunRead>(response);
    },
    async getRunByFingerprint(fingerprint, signal) {
      const response = await productFetch(
        `${RUNS_PREFIX}/fingerprint/${encodeURIComponent(fingerprint)}`,
        { method: "GET", signal },
        deps,
      );
      return readJsonOrThrow<IntelligenceRunRead>(response);
    },
    async getLatestDashboardCapable(signal) {
      const response = await productFetch(
        `${RUNS_PREFIX}/latest-dashboard-capable`,
        { method: "GET", signal },
        deps,
      );
      return readJsonOrThrow<IntelligenceRunRead>(response);
    },
    async getRunDashboard(runId, signal) {
      const response = await productFetch(
        `${RUNS_PREFIX}/id/${encodeURIComponent(runId)}/dashboard`,
        { method: "GET", signal },
        deps,
      );
      return readJsonOrThrow<IntelligenceRunDashboardRead>(response);
    },
    async getRunHumanReview(runId, signal) {
      const response = await productFetch(
        `${RUNS_PREFIX}/id/${encodeURIComponent(runId)}/human-review`,
        { method: "GET", signal },
        deps,
      );
      return readJsonOrThrow<IntelligenceRunHumanReviewRead>(response);
    },
    async getRunAde(runId, signal) {
      const response = await productFetch(
        `${RUNS_PREFIX}/id/${encodeURIComponent(runId)}/ade`,
        { method: "GET", signal },
        deps,
      );
      return readJsonOrThrow<IntelligenceRunAdeRead>(response);
    },
    async postBootstrapToken(signal) {
      return requestBootstrapToken({
        fetchImpl: deps.fetchImpl,
        signal,
        apiBaseUrl: deps.apiBaseUrl,
      });
    },
  };
}

/** Compile-time / runtime inventory of exposed client methods. */
export const INTELLIGENCE_CLIENT_METHODS = [
  "getRunById",
  "getRunByFingerprint",
  "getLatestDashboardCapable",
  "getRunDashboard",
  "getRunHumanReview",
  "getRunAde",
  "postBootstrapToken",
] as const;

export const BOOTSTRAP_ONLY_MUTATION_PATH = BOOTSTRAP_PATH;
