"use client";

import { Menu, X } from "lucide-react";
import { useState } from "react";
import { EnvironmentBadge } from "@/components/shell/environment-badge";
import { SidebarNav } from "@/components/shell/sidebar-nav";
import { ThemeToggle } from "@/components/shell/theme-toggle";
import { Button } from "@/components/ui/button";
import { useSession } from "@/components/providers/session-provider";

export function TopBar() {
  const { session } = useSession();
  const [mobileOpen, setMobileOpen] = useState(false);
  const environment = session?.environment ?? "paper";

  return (
    <header className="border-b border-[color:var(--border)] bg-[color:var(--surface)]">
      <div className="flex items-center justify-between gap-3 px-4 py-3 md:px-6">
        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            size="icon"
            className="md:hidden"
            aria-expanded={mobileOpen}
            aria-controls="mobile-nav"
            aria-label={mobileOpen ? "Close navigation" : "Open navigation"}
            onClick={() => setMobileOpen((open) => !open)}
          >
            {mobileOpen ? (
              <X className="h-4 w-4" aria-hidden />
            ) : (
              <Menu className="h-4 w-4" aria-hidden />
            )}
          </Button>
          <div>
            <p className="font-[family-name:var(--font-display)] text-lg tracking-tight">
              Platform Console
            </p>
            <p className="text-xs text-[color:var(--muted-fg)]">
              Read-only operations shell
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <EnvironmentBadge environment={environment} />
          <ThemeToggle />
          <div className="hidden text-right sm:block">
            <p className="text-sm font-medium">
              {session?.displayName ?? "Signed out"}
            </p>
            <p className="text-xs text-[color:var(--muted-fg)]">
              {session?.bootstrap ? "Local bootstrap session" : "No session"}
            </p>
          </div>
        </div>
      </div>

      {mobileOpen ? (
        <div
          id="mobile-nav"
          className="border-t border-[color:var(--border)] px-4 py-3 md:hidden"
        >
          <SidebarNav onNavigate={() => setMobileOpen(false)} />
        </div>
      ) : null}
    </header>
  );
}
