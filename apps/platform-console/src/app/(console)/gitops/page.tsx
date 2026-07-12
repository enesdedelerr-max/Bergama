import { ModuleUnavailable } from "@/components/common/module-unavailable";

export default function GitOpsPage() {
  return (
    <ModuleUnavailable
      title="GitOps"
      description="GitOps operational views are not enabled in this shell release."
    />
  );
}
