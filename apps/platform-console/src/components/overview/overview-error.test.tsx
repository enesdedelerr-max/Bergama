import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import { OverviewPage } from "@/components/overview/overview-page";
import { SessionProvider } from "@/components/providers/session-provider";

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams("scenario=error"),
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

describe("OverviewPage error state", () => {
  it("renders the error state with retry", async () => {
    renderOverview();
    expect(await screen.findByTestId("overview-error")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });
});
