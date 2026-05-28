/** Central registry of route paths so navigation stays typo-safe. */
export const routes = {
  home: '/',
  onboarding: '/onboarding',
} as const;

export type RoutePath = (typeof routes)[keyof typeof routes];
