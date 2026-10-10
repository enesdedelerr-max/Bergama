/**
 * In-memory product API token store. No browser persistence.
 */
export type StoredAccessToken = {
  accessToken: string;
  expiresAtMs: number;
  scopes: readonly string[];
};

export class MemoryTokenStore {
  private current: StoredAccessToken | null = null;

  get(): StoredAccessToken | null {
    return this.current;
  }

  set(token: StoredAccessToken): void {
    this.current = {
      accessToken: token.accessToken,
      expiresAtMs: token.expiresAtMs,
      scopes: [...token.scopes],
    };
  }

  clear(): void {
    this.current = null;
  }
}
