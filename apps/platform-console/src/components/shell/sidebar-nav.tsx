"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { CONSOLE_NAV } from "@/components/shell/nav-items";
import { cn } from "@/lib/utils";

export function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <nav aria-label="Primary" className="flex flex-col gap-1">
      {CONSOLE_NAV.map((item) => {
        const active =
          item.href === "/"
            ? pathname === "/"
            : pathname === item.href || pathname.startsWith(`${item.href}/`);

        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            className={cn(
              "rounded-sm px-3 py-2 text-sm transition-colors",
              active
                ? "bg-[color:var(--surface-muted)] font-medium text-[color:var(--foreground)]"
                : "text-[color:var(--muted-fg)] hover:bg-[color:var(--surface-muted)] hover:text-[color:var(--foreground)]",
            )}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
