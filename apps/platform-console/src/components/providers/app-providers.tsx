"use client";

import type { ReactNode } from "react";
import { QueryProvider } from "@/components/providers/query-provider";
import { SessionProvider } from "@/components/providers/session-provider";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { AuthTokenProvider } from "@/lib/auth/auth-token-provider";

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <QueryProvider>
        <SessionProvider>
          <AuthTokenProvider>{children}</AuthTokenProvider>
        </SessionProvider>
      </QueryProvider>
    </ThemeProvider>
  );
}
