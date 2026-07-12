import { ModuleUnavailable } from "@/components/common/module-unavailable";

export default function SettingsPage() {
  return (
    <ModuleUnavailable
      title="Settings"
      description="Console settings beyond local bootstrap session and theme are not enabled in this shell release."
    />
  );
}
