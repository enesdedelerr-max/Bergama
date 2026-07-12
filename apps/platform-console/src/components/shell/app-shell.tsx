import type { ReactNode } from "react";
import { SidebarNav } from "@/components/shell/sidebar-nav";
import { TopBar } from "@/components/shell/top-bar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[color:var(--background)] text-[color:var(--foreground)]">
      <div
        className="pointer-events-none absolute inset-0 -z-10 opacity-70"
        aria-hidden
        style={{
          backgroundImage:
            "radial-gradient(circle at top left, color-mix(in oklab, var(--accent) 18%, transparent), transparent 42%), linear-gradient(180deg, color-mix(in oklab, var(--surface-muted) 55%, transparent), transparent 38%)",
        }}
      />
      <TopBar />
      <div className="mx-auto flex w-full max-w-7xl gap-6 px-4 py-6 md:px-6">
        <aside className="hidden w-56 shrink-0 md:block">
          <div className="sticky top-6 rounded-sm border border-[color:var(--border)] bg-[color:var(--surface)] p-3">
            <p className="mb-3 px-3 text-[11px] font-medium tracking-[0.14em] text-[color:var(--muted-fg)] uppercase">
              Navigation
            </p>
            <SidebarNav />
          </div>
        </aside>
        <main id="main-content" className="min-w-0 flex-1">
          {children}
        </main>
      </div>
    </div>
  );
}
