/** Persistence of the backend session token across reloads. */

const STORAGE_KEY = 'unitkeeper.session';

export interface StoredSession {
  accessToken: string;
  /** ISO timestamp from the backend. */
  expiresAt: string;
}

function isExpired(expiresAt: string): boolean {
  const expiry = Date.parse(expiresAt);
  if (Number.isNaN(expiry)) return false;
  // Treat sessions within a 30s window of expiry as already expired to avoid
  // racing a request that would be rejected mid-flight.
  return expiry - Date.now() <= 30_000;
}

export function loadSession(): StoredSession | null {
  let raw: string | null;
  try {
    raw = localStorage.getItem(STORAGE_KEY);
  } catch {
    // Storage can be unavailable (private mode / blocked); treat as no session.
    return null;
  }
  if (!raw) return null;

  try {
    const parsed = JSON.parse(raw) as Partial<StoredSession>;
    if (!parsed.accessToken || !parsed.expiresAt) return null;
    if (isExpired(parsed.expiresAt)) {
      clearSession();
      return null;
    }
    return { accessToken: parsed.accessToken, expiresAt: parsed.expiresAt };
  } catch {
    return null;
  }
}

export function saveSession(session: StoredSession): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  } catch {
    // Best-effort: a non-persisted session still works for the current load.
  }
}

export function clearSession(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Ignore.
  }
}
