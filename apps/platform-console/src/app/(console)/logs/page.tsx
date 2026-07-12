import { ModuleUnavailable } from "@/components/common/module-unavailable";

export default function LogsPage() {
  return (
    <ModuleUnavailable
      title="Logs"
      description="Log exploration is not enabled in this shell release."
    />
  );
}
