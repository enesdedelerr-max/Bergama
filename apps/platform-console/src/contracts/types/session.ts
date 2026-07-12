export type ConsoleSession = {
  sessionId: string;
  operatorId: string;
  displayName: string;
  role: "viewer";
  environment: "paper" | "sandbox" | "live";
  authenticated: boolean;
  bootstrap: true;
};
