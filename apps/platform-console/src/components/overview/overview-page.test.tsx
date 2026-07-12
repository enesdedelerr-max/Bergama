import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import { OverviewPage } from "@/components/overview/overview-page";
import { SessionProvider } from "@/components/providers/session-provider";

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(),
}));

function renderOverview() {
  const client = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>
      <SessionProvider>{children}</SessionProvider>
    </QueryClientProvider>
  );

  return render(<OverviewPage />, { wrapper });
}

describe("OverviewPage", () => {
  it("renders service cards from the mock overview contract", async () => {
    renderOverview();

    expect(
      await screen.findByRole("heading", { name: "Overview" }),
    ).toBeInTheDocument();
    expect(
      await screen.findByTestId("service-card-kubernetes"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("service-card-sprint1-gate")).toBeInTheDocument();
    expect(screen.getByTestId("overview-status-table")).toBeInTheDocument();
  });
});
