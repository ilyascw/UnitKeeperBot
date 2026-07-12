/** Central registry of route paths so navigation stays typo-safe. */
export const routes = {
  home: '/',
  onboarding: '/onboarding',
  onboardingCreate: '/onboarding/create',
  onboardingJoin: '/onboarding/join',
  dashboard: '/dashboard',
  tasks: '/tasks',
  taskLogs: '/tasks/history',
  progress: '/progress',
  balance: '/balance',
  group: '/group',
  groupSettings: '/group/settings',
  groupWeights: '/group/weights',
} as const;

export type RoutePath = (typeof routes)[keyof typeof routes];
