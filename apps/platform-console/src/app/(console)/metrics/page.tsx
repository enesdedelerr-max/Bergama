import { ModuleUnavailable } from "@/components/common/module-unavailable";

export default function MetricsPage() {
  return (
    <ModuleUnavailable
      title="Metrics"
      description="Metrics exploration is not enabled in this shell release."
    />
  );
}
