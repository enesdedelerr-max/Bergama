"use client";

import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { ConsoleSession } from "@/contracts/types/session";
import { createBootstrapSession } from "@/lib/api/session";

type SessionContextValue = {
  session: ConsoleSession | null;
  signInBootstrap: () => void;
  signOut: () => void;
};

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<ConsoleSession | null>(() =>
    createBootstrapSession(),
  );

  const value = useMemo<SessionContextValue>(
    () => ({
      session,
      signInBootstrap: () => setSession(createBootstrapSession()),
      signOut: () => setSession(null),
    }),
    [session],
  );

  return (
    <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
  );
}

export function useSession(): SessionContextValue {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useSession must be used within SessionProvider");
  }
  return context;
}
