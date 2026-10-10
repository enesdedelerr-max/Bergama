import { expect, test, type Page, type Route } from "@playwright/test";

const API_ORIGIN = "http://127.0.0.1:8000";
const RUN_ID = "run-ws3-smoke-001";
const PRIVATE_ADE_PAYLOAD =
  "PRIVATE_ADE_RECORDED_ATTESTATION_PAYLOAD_MUST_NOT_RENDER";
const HR_ADVERSARIAL_PAYLOAD =
  '<script>window.__hr_e2e=1</script><img src=x onerror="window.__hr_e2e=1">safe-hr-text';

function encodeJwt(scopes: string[]): string {
  const header = Buffer.from(
    JSON.stringify({ alg: "none", typ: "JWT" }),
  ).toString("base64url");
  const payload = Buffer.from(JSON.stringify({ scopes, jti: "e2e" })).toString(
    "base64url",
  );
  return `${header}.${payload}.sig`;
}

const ACCESS_TOKEN = encodeJwt(["intelligence:runs:read", "api:read"]);

const latestRun = {
  run_id: RUN_ID,
  pipeline_fingerprint: "ab".repeat(32),
  as_of: "2026-10-10T12:00:00Z",
  persisted_at: "2026-10-10T12:05:00Z",
  age_seconds: 42,
  outcome: "completed",
  snapshot_contract_version: "v1",
  persistence_schema_version: "v1",
  stage_presence: {
    dashboard: "present",
    human_review: "present",
    ade: "present",
  },
  provenance: {},
};

const dashboardBody = {
  run_id: RUN_ID,
  dashboard: {
    dashboard_output_id: "d".repeat(64),
    policy_version_id: "dash-pol",
    ordering_preservation_policy_id: "ord",
    presentation_selection_policy_id: "pres",
    as_of: "2026-10-10T12:00:00Z",
    records: [],
    provenance: {},
  },
};

const humanReviewBody = {
  run_id: RUN_ID,
  human_review: {
    human_review_output_id: "hr-1",
    policy_version_id: "hr-policy",
    ordering_preservation_policy_id: "ord",
    presentation_preservation_policy_id: "pres",
    human_attestation_policy_id: "att",
    identity_specification_id: "id",
    provenance_specification_id: "prov",
    history_specification_id: "hist",
    as_of: "2026-10-10T12:00:00Z",
    dashboard_output_id: "c".repeat(64),
    records: [{ should_not_render: true }],
    attestation: { recorded_payload: HR_ADVERSARIAL_PAYLOAD },
    provenance: {},
    history: {},
  },
};

const adeBody = {
  run_id: RUN_ID,
  ade: {
    outcome_kind: "accepted",
    policy_version_id: "ade-policy",
    as_of: "2026-10-10T12:00:00Z",
    reason_family: "policy",
    decision_id: "decision-1",
    human_review_output_id: "hr-1",
    detail: "recorded detail",
    recorded_attestation_payload: PRIVATE_ADE_PAYLOAD,
    provenance: {
      policy_version_id: "ade-policy",
      identity_specification_id: "id-spec",
      provenance_specification_id: "prov-spec",
      acceptance_specification_id: "acc-spec",
      digest_method_id: "digest",
      derivation_attribution_id: "deriv",
      as_of: "2026-10-10T12:00:00Z",
      recorded_attestation_fingerprint: "fp".padEnd(64, "0"),
      config_fingerprint: "cf".padEnd(64, "1"),
      evidence_fingerprint: "ef".padEnd(64, "2"),
      recorded_attestation_payload: PRIVATE_ADE_PAYLOAD,
    },
  },
};

async function fulfillJson(
  route: Route,
  status: number,
  body: unknown,
): Promise<void> {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function installProductApiMocks(
  page: Page,
  options?: { failClosedLatest?: boolean },
): Promise<void> {
  await page.route(`${API_ORIGIN}/api/v1/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;

    if (path === "/api/v1/auth/token" && request.method() === "POST") {
      await fulfillJson(route, 200, {
        access_token: ACCESS_TOKEN,
        token_type: "bearer",
        expires_in: 900,
      });
      return;
    }

    if (
      path === "/api/v1/intelligence/runs/latest-dashboard-capable" &&
      request.method() === "GET"
    ) {
      if (options?.failClosedLatest) {
        await fulfillJson(route, 503, {
          code: "intelligence.runs.storage_unavailable",
          message: "storage unavailable",
          request_id: "e2e-storage",
        });
        return;
      }
      await fulfillJson(route, 200, latestRun);
      return;
    }

    if (
      path === `/api/v1/intelligence/runs/id/${RUN_ID}` &&
      request.method() === "GET"
    ) {
      await fulfillJson(route, 200, latestRun);
      return;
    }

    if (
      path === `/api/v1/intelligence/runs/id/${RUN_ID}/dashboard` &&
      request.method() === "GET"
    ) {
      await fulfillJson(route, 200, dashboardBody);
      return;
    }

    if (
      path === `/api/v1/intelligence/runs/id/${RUN_ID}/human-review` &&
      request.method() === "GET"
    ) {
      await fulfillJson(route, 200, humanReviewBody);
      return;
    }

    if (
      path === `/api/v1/intelligence/runs/id/${RUN_ID}/ade` &&
      request.method() === "GET"
    ) {
      await fulfillJson(route, 200, adeBody);
      return;
    }

    await fulfillJson(route, 404, {
      code: "not.found",
      message: `unmocked ${path}`,
      request_id: "e2e-unmocked",
    });
  });
}

async function assertNoWriteControls(page: Page): Promise<void> {
  await expect(
    page.getByRole("button", {
      name: /approve|reject|submit|execute|trade|invoke model|broker/i,
    }),
  ).toHaveCount(0);
  await expect(page.getByRole("link", { name: /buy|sell|trade|broker/i })).toHaveCount(
    0,
  );
  await expect(page.getByText(/safe-to-trade|place order|submit order/i)).toHaveCount(
    0,
  );
}

test.describe("Premarket smoke", () => {
  test("loads Premarket, authenticates, navigates run detail, and stays read-only", async ({
    page,
  }) => {
    await installProductApiMocks(page);

    const response = await page.goto("/premarket");
    expect(response).not.toBeNull();
    expect(response?.headers()["x-content-type-options"]?.toLowerCase()).toBe(
      "nosniff",
    );
    expect(response?.headers()["x-frame-options"]?.toUpperCase()).toBe("DENY");

    await expect(page.getByRole("heading", { name: "Premarket" })).toBeVisible();
    await expect(page.getByTestId("premarket-landing")).toBeVisible();
    await expect(page.locator('[data-ux-state="unauthenticated"]')).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Acquire bootstrap token" }),
    ).toBeVisible();

    await page.getByRole("button", { name: "Acquire bootstrap token" }).click();
    await expect(
      page.getByTestId("premarket-latest-success"),
    ).toBeVisible();
    await expect(page.getByText(RUN_ID)).toBeVisible();
    await assertNoWriteControls(page);

    await page.getByRole("link", { name: "Open run detail" }).click();
    await expect(page).toHaveURL(new RegExp(`/premarket/runs/${RUN_ID}$`));
    await expect(page.getByTestId("premarket-run-detail")).toBeVisible();
    await expect(page.getByTestId("premarket-dashboard-panel")).toBeVisible();

    const hrPayload = page.getByTestId("premarket-hr-payload");
    await expect(hrPayload).toBeVisible();
    await expect(hrPayload).toContainText("safe-hr-text");
    await expect(hrPayload).toContainText("<script>");
    await expect(hrPayload.locator("script")).toHaveCount(0);
    await expect(hrPayload.locator("img")).toHaveCount(0);

    const adePanel = page.getByTestId("premarket-ade-panel");
    await expect(adePanel).toBeVisible();
    await expect(adePanel).toContainText("accepted");
    await expect(adePanel).not.toContainText(PRIVATE_ADE_PAYLOAD);
    await expect(page.getByText(/recorded_attestation_payload/i)).toHaveCount(0);

    await assertNoWriteControls(page);
  });

  test("presents a critical fail-closed storage error on latest path", async ({
    page,
  }) => {
    await installProductApiMocks(page, { failClosedLatest: true });
    await page.goto("/premarket");
    await page.getByRole("button", { name: "Acquire bootstrap token" }).click();
    const storageAlert = page.getByTestId("premarket-storage_unavailable");
    await expect(storageAlert).toBeVisible();
    await expect(storageAlert).toContainText(/storage|unavailable/i);
    await assertNoWriteControls(page);
  });
});
