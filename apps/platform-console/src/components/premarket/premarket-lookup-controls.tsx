"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { createIntelligenceClient } from "@/lib/api/intelligence-client";
import { ApiClientError } from "@/lib/api/errors";
import { useAuthToken } from "@/lib/auth/auth-token-provider";
import { mapProductErrorToUxState } from "@/lib/premarket/map-product-error";
import { normalizePipelineFingerprint } from "@/lib/premarket/ux-states";
import {
  PremarketFailClosedError,
  PremarketProductFaultState,
  PremarketRunNotFoundState,
} from "@/components/premarket/premarket-states";

export function PremarketLookupControls({ enabled }: { enabled: boolean }) {
  const router = useRouter();
  const auth = useAuthToken();
  const [runIdInput, setRunIdInput] = useState("");
  const [fingerprintInput, setFingerprintInput] = useState("");
  const [fingerprintLocalError, setFingerprintLocalError] = useState<
    string | null
  >(null);
  const [fingerprintBusy, setFingerprintBusy] = useState(false);
  const [fingerprintError, setFingerprintError] = useState<unknown>(null);

  function onRunIdSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = runIdInput.trim();
    if (!trimmed || !enabled) {
      return;
    }
    router.push(`/premarket/runs/${encodeURIComponent(trimmed)}`);
  }

  async function onFingerprintSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFingerprintLocalError(null);
    setFingerprintError(null);

    if (!enabled) {
      return;
    }

    const normalized = normalizePipelineFingerprint(fingerprintInput);
    if (!normalized.ok) {
      if (normalized.reason === "empty") {
        return;
      }
      setFingerprintLocalError(
        "Fingerprint must be exactly 64 lowercase hexadecimal characters.",
      );
      return;
    }

    setFingerprintBusy(true);
    try {
      const client = createIntelligenceClient({
        getAccessToken: auth.getAccessToken,
        getAuthGeneration: auth.getAuthGeneration,
        reacquireOnce: auth.reacquireOnce,
        onForbidden: auth.markInsufficientScope,
      });
      const run = await client.getRunByFingerprint(normalized.fingerprint);
      router.push(`/premarket/runs/${encodeURIComponent(run.run_id)}`);
    } catch (error) {
      setFingerprintError(error);
    } finally {
      setFingerprintBusy(false);
    }
  }

  const fingerprintUx = fingerprintError
    ? mapProductErrorToUxState(fingerprintError, "fingerprint")
    : null;

  return (
    <section
      aria-labelledby="premarket-lookup-heading"
      data-testid="premarket-lookup-controls"
      className="space-y-4"
    >
      <h2 id="premarket-lookup-heading" className="text-base font-semibold">
        Lookup persisted run
      </h2>

      <Card>
        <CardHeader>
          <CardTitle>Run ID</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={onRunIdSubmit}
            className="flex flex-col gap-3 sm:flex-row sm:items-end"
          >
            <div className="flex-1 space-y-1">
              <label htmlFor="premarket-run-id" className="text-xs font-medium">
                Run ID
              </label>
              <input
                id="premarket-run-id"
                name="runId"
                type="text"
                autoComplete="off"
                disabled={!enabled}
                value={runIdInput}
                onChange={(event) => setRunIdInput(event.target.value)}
                className="w-full rounded-sm border border-[color:var(--border)] bg-[color:var(--surface)] px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--accent)]"
              />
            </div>
            <Button type="submit" disabled={!enabled}>
              Open run
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Pipeline fingerprint</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <form
            onSubmit={onFingerprintSubmit}
            className="flex flex-col gap-3 sm:flex-row sm:items-end"
          >
            <div className="flex-1 space-y-1">
              <label
                htmlFor="premarket-fingerprint"
                className="text-xs font-medium"
              >
                Fingerprint (64-char lowercase hex)
              </label>
              <input
                id="premarket-fingerprint"
                name="fingerprint"
                type="text"
                autoComplete="off"
                spellCheck={false}
                disabled={!enabled || fingerprintBusy}
                value={fingerprintInput}
                onChange={(event) => setFingerprintInput(event.target.value)}
                className="w-full rounded-sm border border-[color:var(--border)] bg-[color:var(--surface)] px-3 py-2 font-mono text-sm outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--accent)]"
              />
            </div>
            <Button type="submit" disabled={!enabled || fingerprintBusy}>
              {fingerprintBusy ? "Looking up…" : "Lookup fingerprint"}
            </Button>
          </form>
          {fingerprintLocalError ? (
            <p
              role="alert"
              data-testid="premarket-fingerprint-invalid"
              className="text-sm text-[color:var(--muted-fg)]"
            >
              {fingerprintLocalError}
            </p>
          ) : null}
          {fingerprintUx === "run_not_found" ? (
            <PremarketRunNotFoundState />
          ) : null}
          {fingerprintUx === "unsupported_snapshot_contract" ? (
            <PremarketProductFaultState
              state="unsupported_snapshot_contract"
              title="Unsupported snapshot contract"
              error={fingerprintError}
            />
          ) : null}
          {fingerprintUx === "corrupt_persisted_snapshot" ? (
            <PremarketProductFaultState
              state="corrupt_persisted_snapshot"
              title="Corrupt persisted snapshot"
              error={fingerprintError}
            />
          ) : null}
          {fingerprintUx === "storage_unavailable" ? (
            <PremarketProductFaultState
              state="storage_unavailable"
              title="Storage unavailable"
              error={fingerprintError}
            />
          ) : null}
          {fingerprintUx === "network_unavailable" ? (
            <PremarketProductFaultState
              state="network_unavailable"
              title="Network unavailable"
              error={fingerprintError}
            />
          ) : null}
          {fingerprintUx === "insufficient_scope" ? (
            <p role="alert" className="text-sm text-[color:var(--muted-fg)]">
              Insufficient product scope for fingerprint lookup.
            </p>
          ) : null}
          {fingerprintError &&
          fingerprintUx === null &&
          !(
            fingerprintError instanceof ApiClientError &&
            fingerprintError.status === 401
          ) ? (
            <PremarketFailClosedError error={fingerprintError} />
          ) : null}
        </CardContent>
      </Card>
    </section>
  );
}
