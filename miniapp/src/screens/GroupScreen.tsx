import { Button, Cell, Info, List, Section } from '@telegram-apps/telegram-ui';
import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';

import { useLeaveGroup } from '@/api/mutations';
import { useCurrentGroup } from '@/api/queries';
import { useAuth } from '@/auth/useAuth';
import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';
import { routes } from '@/routes/paths';

const WEEKDAY_LABEL: Record<string, string> = {
  monday: 'Monday',
  tuesday: 'Tuesday',
  wednesday: 'Wednesday',
  thursday: 'Thursday',
  friday: 'Friday',
  saturday: 'Saturday',
  sunday: 'Sunday',
};

function memberName(member: { first_name: string | null; username: string | null; user_id: number }): string {
  return member.first_name ?? member.username ?? `User ${member.user_id}`;
}

/**
 * Main group surface. Shows the legacy `/group_info` payload (members, weights,
 * sprint window, group balance) plus an owner-marked settings entry and an
 * explicit "leave group" flow that surfaces the owner-handover policy.
 */
export function GroupScreen() {
  const navigate = useNavigate();
  const { context } = useAuth();
  const { data: group, isPending, isError, error, refetch } = useCurrentGroup();
  const leave = useLeaveGroup();
  const [confirmingLeave, setConfirmingLeave] = useState(false);

  if (isPending) return <Loader label="Loading your group…" />;
  if (isError) {
    return <ErrorState description={error.message} onRetry={() => void refetch()} />;
  }
  if (group === null) {
    return <Navigate to={routes.onboarding} replace />;
  }

  const myUserId = context?.user?.id;
  const isOwner = myUserId === group.owner_user_id;
  const otherMembers = group.members.filter((m) => m.user_id !== myUserId);
  // Backend transfers ownership to the active member with the lowest user_id
  // when the owner leaves; mirror that here so the warning matches reality.
  const handoverTo =
    isOwner && otherMembers.length > 0
      ? [...otherMembers].sort((a, b) => a.user_id - b.user_id)[0]
      : null;

  const onConfirmLeave = (): void => {
    leave.mutate(undefined, { onSuccess: () => navigate(routes.onboarding, { replace: true }) });
  };

  return (
    <List>
      <Section header={group.name} footer={`Timezone: ${group.timezone}`}>
        <Cell subtitle="Group balance">
          <Info type="text">{group.group_balance}</Info>
        </Cell>
        {isOwner ? (
          <Cell subtitle="Join secret (owner only)">
            <Info type="text">{group.join_secret ?? '—'}</Info>
          </Cell>
        ) : null}
      </Section>

      <Section header="Sprint">
        <Cell subtitle="Starts on">{WEEKDAY_LABEL[group.sprint_start_weekday] ?? group.sprint_start_weekday}</Cell>
        <Cell subtitle="Duration">{group.sprint_duration_days} days</Cell>
        <Cell subtitle="Current period">
          {group.sprint_period_start} → {group.sprint_period_end}
        </Cell>
        <Cell subtitle="Ends at">{new Date(group.sprint_ends_at).toLocaleString()}</Cell>
      </Section>

      <Section header={`Members (${group.members.length})`}>
        {group.members.map((member) => (
          <Cell
            key={member.user_id}
            subtitle={
              member.is_owner
                ? `Owner · weight ${member.weight_percent}%`
                : `Weight ${member.weight_percent}%`
            }
            after={<Info type="text">{member.balance}</Info>}
          >
            {memberName(member)}
            {member.user_id === myUserId ? ' (you)' : ''}
          </Cell>
        ))}
      </Section>

      {isOwner ? (
        <Section header="Owner actions">
          <Cell onClick={() => navigate(routes.groupSettings)}>Group settings</Cell>
          <Cell onClick={() => navigate(routes.groupWeights)}>Edit weights</Cell>
        </Section>
      ) : null}

      <Section header="Leave group">
        {confirmingLeave ? (
          <>
            <div style={{ padding: '8px 16px', fontSize: 14 }}>
              {handoverTo ? (
                <>
                  You are the owner. Leaving will transfer ownership to{' '}
                  <strong>{memberName(handoverTo)}</strong>. Continue?
                </>
              ) : isOwner ? (
                <>You are the only member. Leaving will permanently dissolve this group.</>
              ) : (
                <>You will lose access to this group and need the secret to rejoin.</>
              )}
            </div>
            {leave.isError ? (
              <div
                style={{
                  padding: '8px 16px',
                  color: 'var(--tgui--destructive_text_color)',
                }}
              >
                {leave.error.message}
              </div>
            ) : null}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: '8px 16px' }}>
              <Button
                stretched
                size="l"
                mode="filled"
                loading={leave.isPending}
                onClick={onConfirmLeave}
              >
                Confirm leave
              </Button>
              <Button
                stretched
                size="l"
                mode="plain"
                disabled={leave.isPending}
                onClick={() => setConfirmingLeave(false)}
              >
                Cancel
              </Button>
            </div>
          </>
        ) : (
          <div style={{ padding: '8px 16px' }}>
            <Button stretched size="l" mode="outline" onClick={() => setConfirmingLeave(true)}>
              Leave group
            </Button>
          </div>
        )}
      </Section>
    </List>
  );
}
