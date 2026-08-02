/** Deterministic avatar/segment colors, keyed off a stable seed (user id). */
const AVATAR_COLORS = ['#e12e2a', '#2159c9', '#ffd93b', '#3fbe5b', '#8c9098'];

export function avatarColor(seed: number): string {
  return AVATAR_COLORS[Math.abs(seed) % AVATAR_COLORS.length];
}
