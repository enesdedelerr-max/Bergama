import { ModuleUnavailable } from "@/components/common/module-unavailable";

export default function InfrastructurePage() {
  return (
    <ModuleUnavailable
      title="Infrastructure"
      description="Infrastructure detail views are not enabled in this shell release. Use Overview for current mock health status."
    />
  );
}
