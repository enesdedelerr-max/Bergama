import { ModuleUnavailable } from "@/components/common/module-unavailable";

export default function ReleasesPage() {
  return (
    <ModuleUnavailable
      title="Releases"
      description="Release inventory views are not enabled in this shell release."
    />
  );
}
