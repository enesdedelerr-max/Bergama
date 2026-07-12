export const CONSOLE_NAV = [
  { href: "/", label: "Overview" },
  { href: "/infrastructure", label: "Infrastructure" },
  { href: "/data-services", label: "Data Services" },
  { href: "/gitops", label: "GitOps" },
  { href: "/releases", label: "Releases" },
  { href: "/logs", label: "Logs" },
  { href: "/metrics", label: "Metrics" },
  { href: "/settings", label: "Settings" },
] as const;

export type ConsoleNavItem = (typeof CONSOLE_NAV)[number];
