/** Central registry of route paths so navigation stays typo-safe. */
export const routes = {
  home: '/',
  onboarding: '/onboarding',
  onboardingCreate: '/onboarding/create',
  onboardingJoin: '/onboarding/join',
  group: '/group',
  groupSettings: '/group/settings',
  groupWeights: '/group/weights',
} as const;

export type RoutePath = (typeof routes)[keyof typeof routes];
