import type { PlatformEnvironment } from "@/contracts/types/platform-health";
import { Badge } from "@/components/ui/badge";

const ENV_LABEL: Record<PlatformEnvironment, string> = {
  paper: "Paper",
  sandbox: "Sandbox",
  live: "Live",
};

export function EnvironmentBadge({
  environment,
}: {
  environment: PlatformEnvironment;
}) {
  return (
    <Badge
      tone={environment}
      aria-label={`Environment: ${ENV_LABEL[environment]}`}
    >
      {ENV_LABEL[environment]}
    </Badge>
  );
}
