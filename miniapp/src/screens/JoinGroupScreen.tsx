import { Button, Input, List, Section } from '@telegram-apps/telegram-ui';
import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';

import { useJoinGroup } from '@/api/mutations';
import { routes } from '@/routes/paths';

/**
 * Joins an existing group by name and secret. Mirrors legacy `/join_group`.
 */
export function JoinGroupScreen() {
  const navigate = useNavigate();
  const mutation = useJoinGroup();

  const [name, setName] = useState('');
  const [secret, setSecret] = useState('');

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    mutation.mutate(
      { name: name.trim(), join_secret: secret },
      { onSuccess: () => navigate(routes.group, { replace: true }) },
    );
  };

  const disabled = mutation.isPending || name.trim().length === 0 || secret.length < 3;

  return (
    <form onSubmit={handleSubmit}>
      <List>
        <Section
          header="Join a group"
          footer="Ask the owner for the group name and the join secret."
        >
          <Input
            header="Group name"
            value={name}
            onChange={(event) => setName(event.currentTarget.value)}
            disabled={mutation.isPending}
          />
          <Input
            header="Join secret"
            value={secret}
            onChange={(event) => setSecret(event.currentTarget.value)}
            disabled={mutation.isPending}
          />
        </Section>
        {mutation.isError ? (
          <Section header="Couldn’t join group">
            <div style={{ padding: '8px 16px', color: 'var(--tgui--destructive_text_color)' }}>
              {mutation.error.message}
            </div>
          </Section>
        ) : null}
        <Section>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: '8px 16px' }}>
            <Button type="submit" stretched size="l" loading={mutation.isPending} disabled={disabled}>
              Join group
            </Button>
            <Button
              type="button"
              stretched
              size="l"
              mode="plain"
              onClick={() => navigate(routes.onboarding)}
              disabled={mutation.isPending}
            >
              Cancel
            </Button>
          </div>
        </Section>
      </List>
    </form>
  );
}
