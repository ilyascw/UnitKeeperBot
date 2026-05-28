import { Button, Input, List, Section, Select } from '@telegram-apps/telegram-ui';
import { useEffect, useState, type FormEvent } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';

import { useUpdateGroupSettings } from '@/api/mutations';
import { useCurrentGroup } from '@/api/queries';
import { WEEKDAYS, type Weekday } from '@/api/types';
import { useAuth } from '@/auth/useAuth';
import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';
import { routes } from '@/routes/paths';

const WEEKDAY_LABEL: Record<Weekday, string> = {
  monday: 'Monday',
  tuesday: 'Tuesday',
  wednesday: 'Wednesday',
  thursday: 'Thursday',
  friday: 'Friday',
  saturday: 'Saturday',
  sunday: 'Sunday',
};

/**
 * Owner-only screen to edit join secret, sprint start weekday and sprint
 * duration. Mirrors the legacy `/group_settings` handler. Non-owners are
 * redirected to the group surface so the route is safe to deep-link to.
 */
export function GroupSettingsScreen() {
  const navigate = useNavigate();
  const { context } = useAuth();
  const { data: group, isPending, isError, error, refetch } = useCurrentGroup();
  const mutation = useUpdateGroupSettings();

  const [secret, setSecret] = useState('');
  const [weekday, setWeekday] = useState<Weekday>('monday');
  const [duration, setDuration] = useState('7');

  // Hydrate inputs once the group card arrives — we can't init from a query
  // that may still be pending, so do it in an effect keyed on the group id.
  useEffect(() => {
    if (!group) return;
    setSecret(group.join_secret ?? '');
    setWeekday(group.sprint_start_weekday as Weekday);
    setDuration(String(group.sprint_duration_days));
  }, [group?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (isPending) return <Loader label="Loading settings…" />;
  if (isError) {
    return <ErrorState description={error.message} onRetry={() => void refetch()} />;
  }
  if (group === null) return <Navigate to={routes.onboarding} replace />;

  const isOwner = context?.user?.id === group.owner_user_id;
  if (!isOwner) return <Navigate to={routes.group} replace />;

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    const days = Number.parseInt(duration, 10);
    if (!Number.isFinite(days) || days <= 0) return;
    mutation.mutate(
      {
        join_secret: secret !== group.join_secret ? secret : undefined,
        sprint_start_weekday: weekday !== group.sprint_start_weekday ? weekday : undefined,
        sprint_duration_days: days !== group.sprint_duration_days ? days : undefined,
      },
      { onSuccess: () => navigate(routes.group) },
    );
  };

  return (
    <form onSubmit={handleSubmit}>
      <List>
        <Section header="Join secret" footer="Members will need this to join the group.">
          <Input
            value={secret}
            onChange={(event) => setSecret(event.currentTarget.value)}
            disabled={mutation.isPending}
          />
        </Section>
        <Section header="Sprint">
          <Select
            header="Start weekday"
            value={weekday}
            onChange={(event) => setWeekday(event.currentTarget.value as Weekday)}
            disabled={mutation.isPending}
          >
            {WEEKDAYS.map((day) => (
              <option key={day} value={day}>
                {WEEKDAY_LABEL[day]}
              </option>
            ))}
          </Select>
          <Input
            header="Duration (days)"
            type="number"
            inputMode="numeric"
            value={duration}
            onChange={(event) => setDuration(event.currentTarget.value)}
            disabled={mutation.isPending}
          />
        </Section>
        {mutation.isError ? (
          <Section header="Couldn’t save">
            <div style={{ padding: '8px 16px', color: 'var(--tgui--destructive_text_color)' }}>
              {mutation.error.message}
            </div>
          </Section>
        ) : null}
        <Section>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: '8px 16px' }}>
            <Button type="submit" stretched size="l" loading={mutation.isPending}>
              Save changes
            </Button>
            <Button
              type="button"
              stretched
              size="l"
              mode="plain"
              onClick={() => navigate(routes.group)}
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
