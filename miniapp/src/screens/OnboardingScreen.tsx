import { Placeholder } from '@telegram-apps/telegram-ui';

/**
 * Placeholder onboarding surface shown when the signed-in user has no group.
 * The create/join group flows are built in Issue 02; this exists so the
 * foundation's routing and "no group" branch are wired end to end.
 */
export function OnboardingScreen() {
  return (
    <div style={{ minHeight: '80vh', display: 'flex', alignItems: 'center' }}>
      <Placeholder
        header="Welcome to UnitKeeper"
        description="You’re not in a group yet. Creating and joining groups arrives in the next release."
      />
    </div>
  );
}
