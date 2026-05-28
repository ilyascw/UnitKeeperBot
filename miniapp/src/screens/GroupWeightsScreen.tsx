import { Button, Input, List, Section } from '@telegram-apps/telegram-ui';
import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';

import { useUpdateGroupWeights } from '@/api/mutations';
import { useCurrentGroup } from '@/api/queries';
import { useAuth } from '@/auth/useAuth';
import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';
import { routes } from '@/routes/paths';

function parsePercent(value: string): number {
  const n = Number.parseFloat(value);
  return Number.isFinite(n) ? n : 0;
}

/**
 * Owner-only editor for member weights. The backend enforces the sum=100 and
 * non-negative invariants, but we surface a live total here so the owner can
 * fix obvious mistakes before submitting.
 */
export function GroupWeightsScreen() {
  const navigate = useNavigate();
  const { context } = useAuth();
  const { data: group, isPending, isError, error, refetch } = useCurrentGroup();
  const mutation = useUpdateGroupWeights();

  const [values, setValues] = useState<Record<number, string>>({});

  useEffect(() => {
    if (!group) return;
    setValues(
      Object.fromEntries(group.members.map((m) => [m.user_id, m.weight_percent])),
    );
  }, [group?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const total = useMemo(
    () => Object.values(values).reduce((acc, value) => acc + parsePercent(value), 0),
    [values],
  );

  if (isPending) return <Loader label="Loading members…" />;
  if (isError) {
    return <ErrorState description={error.message} onRetry={() => void refetch()} />;
  }
  if (group === null) return <Navigate to={routes.onboarding} replace />;

  const isOwner = context?.user?.id === group.owner_user_id;
  if (!isOwner) return <Navigate to={routes.group} replace />;

  const sumIsValid = Math.abs(total - 100) < 0.01;

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    if (!sumIsValid) return;
    mutation.mutate(
      {
        weights: group.members.map((member) => ({
          user_id: member.user_id,
          weight_percent: values[member.user_id] ?? '0',
        })),
      },
      { onSuccess: () => navigate(routes.group) },
    );
  };

  return (
    <form onSubmit={handleSubmit}>
      <List>
        <Section
          header="Member weights"
          footer={`Total: ${total.toFixed(2)}% — must equal 100% to save.`}
        >
          {group.members.map((member) => (
            <Input
              key={member.user_id}
              header={member.first_name ?? member.username ?? `User ${member.user_id}`}
              type="number"
              inputMode="decimal"
              value={values[member.user_id] ?? ''}
              onChange={(event) =>
                setValues((prev) => ({ ...prev, [member.user_id]: event.currentTarget.value }))
              }
              disabled={mutation.isPending}
            />
          ))}
        </Section>
        {mutation.isError ? (
          <Section header="Couldn’t save weights">
            <div style={{ padding: '8px 16px', color: 'var(--tgui--destructive_text_color)' }}>
              {mutation.error.message}
            </div>
          </Section>
        ) : null}
        <Section>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: '8px 16px' }}>
            <Button
              type="submit"
              stretched
              size="l"
              loading={mutation.isPending}
              disabled={!sumIsValid}
            >
              Save weights
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
