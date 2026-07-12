import { Suspense } from "react";
import { OverviewPage } from "@/components/overview/overview-page";
import { OverviewLoadingState } from "@/components/overview/overview-states";

export default function Page() {
  return (
    <Suspense fallback={<OverviewLoadingState />}>
      <OverviewPage />
    </Suspense>
  );
}
