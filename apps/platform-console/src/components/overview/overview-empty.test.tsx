import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import { OverviewPage } from "@/components/overview/overview-page";
import { SessionProvider } from "@/components/providers/session-provider";

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams("scenario=empty"),
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

describe("OverviewPage empty state", () => {
  it("renders the empty inventory state", async () => {
    renderOverview();
    expect(await screen.findByTestId("overview-empty")).toBeInTheDocument();
    expect(screen.getByText("No services reported")).toBeInTheDocument();
  });
});
