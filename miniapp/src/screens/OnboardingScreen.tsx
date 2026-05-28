import { Button, Placeholder } from '@telegram-apps/telegram-ui';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '@/auth/useAuth';
import { routes } from '@/routes/paths';

/**
 * Landing for users without a group. Offers the two entry points covered by
 * Issue 02: create a brand-new group or join an existing one by name + secret.
 * Replaces the legacy `/start` + `/create_group` + `/join_group` flow.
 */
export function OnboardingScreen() {
  const navigate = useNavigate();
  const { context } = useAuth();
  const name = context?.user?.first_name ?? context?.user?.username ?? 'there';

  return (
    <div style={{ minHeight: '70vh', display: 'flex', alignItems: 'center' }}>
      <Placeholder
        header={`Welcome, ${name}`}
        description="You're not in a group yet. Create one to invite others, or join an existing group with its name and secret."
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, width: '100%' }}>
          <Button stretched size="l" onClick={() => navigate(routes.onboardingCreate)}>
            Create group
          </Button>
          <Button
            stretched
            size="l"
            mode="outline"
            onClick={() => navigate(routes.onboardingJoin)}
          >
            Join group
          </Button>
        </div>
      </Placeholder>
    </div>
  );
}
