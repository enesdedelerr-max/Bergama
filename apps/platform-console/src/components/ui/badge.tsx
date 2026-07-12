import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-sm border px-2 py-0.5 text-xs font-medium tracking-wide uppercase",
  {
    variants: {
      tone: {
        success:
          "border-[color:var(--status-success-border)] bg-[color:var(--status-success-bg)] text-[color:var(--status-success-fg)]",
        warning:
          "border-[color:var(--status-warning-border)] bg-[color:var(--status-warning-bg)] text-[color:var(--status-warning-fg)]",
        danger:
          "border-[color:var(--status-danger-border)] bg-[color:var(--status-danger-bg)] text-[color:var(--status-danger-fg)]",
        muted:
          "border-[color:var(--border)] bg-[color:var(--surface-muted)] text-[color:var(--muted-fg)]",
        info: "border-[color:var(--status-info-border)] bg-[color:var(--status-info-bg)] text-[color:var(--status-info-fg)]",
        paper:
          "border-[color:var(--env-paper-border)] bg-[color:var(--env-paper-bg)] text-[color:var(--env-paper-fg)]",
        sandbox:
          "border-[color:var(--env-sandbox-border)] bg-[color:var(--env-sandbox-bg)] text-[color:var(--env-sandbox-fg)]",
        live: "border-[color:var(--env-live-border)] bg-[color:var(--env-live-bg)] text-[color:var(--env-live-fg)]",
      },
    },
    defaultVariants: {
      tone: "muted",
    },
  },
);

type BadgeProps = HTMLAttributes<HTMLSpanElement> &
  VariantProps<typeof badgeVariants>;

export function Badge({ className, tone, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ tone }), className)} {...props} />;
}
