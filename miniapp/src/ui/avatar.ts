/** Deterministic avatar/segment gradients, keyed off a stable seed (user id). */
const AVATAR_GRADIENTS = [
  'linear-gradient(150deg,#5ee0d0,#5aa0ff)',
  'linear-gradient(150deg,#ffb27a,#ff789c)',
  'linear-gradient(150deg,#a78bff,#5aa0ff)',
  'linear-gradient(150deg,#7fe0ff,#5ee0d0)',
  'linear-gradient(150deg,#ff789c,#a78bff)',
];

export function avatarGradient(seed: number): string {
  return AVATAR_GRADIENTS[Math.abs(seed) % AVATAR_GRADIENTS.length];
}
