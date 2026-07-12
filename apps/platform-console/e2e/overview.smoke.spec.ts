import { expect, test } from "@playwright/test";

test("overview shell renders and remains usable on desktop and mobile", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();
  await expect(page.getByTestId("service-card-kubernetes")).toBeVisible();
  await expect(page.getByText("Platform Console")).toBeVisible();
  await expect(
    page.getByRole("banner").getByLabel("Environment: Paper"),
  ).toBeVisible();
});
