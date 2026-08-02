import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { Navigate, useNavigate } from '@/routes/navigation';

import { useUpdateGroupWeights } from '@/api/mutations';
import { useCurrentGroup } from '@/api/queries';
import { useAuth } from '@/auth/useAuth';
import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';
import { routes } from '@/routes/paths';
import { avatarColor } from '@/ui/avatar';
import { Button, Note, Screen, ScreenHeader } from '@/ui/kit';

function memberName(m: {
  first_name: string | null;
  username: string | null;
  user_id: number;
}): string {
  return m.first_name ?? m.username ?? `Участник ${m.user_id}`;
}

/** Evenly split 100 across `n` members, pushing the rounding remainder onto
 * the first member so the total stays exactly 100. */
function evenSplit(userIds: number[]): Record<number, number> {
  const n = userIds.length;
  if (n === 0) return {};
  const base = Math.floor(100 / n);
  const out: Record<number, number> = {};
  userIds.forEach((id) => (out[id] = base));
  out[userIds[0]] += 100 - base * n;
  return out;
}

/** Set `changedId`'s weight to `rawValue` and rescale the other members
 * proportionally to their current shares so the total stays exactly 100. */
function redistribute(
  prev: Record<number, number>,
  changedId: number,
  rawValue: number,
  memberIds: number[],
): Record<number, number> {
  const value = Math.max(0, Math.min(100, Math.round(rawValue)));
  const others = memberIds.filter((id) => id !== changedId);
  const next: Record<number, number> = { ...prev, [changedId]: value };
  if (others.length === 0) return next;

  const remaining = 100 - value;
  const otherSum = others.reduce((acc, id) => acc + (prev[id] ?? 0), 0);

  if (otherSum === 0) {
    const base = Math.floor(remaining / others.length);
    others.forEach((id) => (next[id] = base));
    next[others[0]] += remaining - base * others.length;
    return next;
  }

  let allocated = 0;
  others.forEach((id) => {
    const share = Math.round(((prev[id] ?? 0) / otherSum) * remaining);
    next[id] = share;
    allocated += share;
  });
  const drift = remaining - allocated;
  if (drift !== 0) {
    const largest = others.reduce((a, b) => (next[a] >= next[b] ? a : b));
    next[largest] += drift;
  }
  return next;
}

/**
 * Owner-only editor for member weights. Weights are shares of the planned load
 * that must sum to 100%. The backend enforces the invariant; we surface a live
 * total plus a visual sum bar and quick "even split" / "reset" actions.
 */
export function GroupWeightsScreen() {
  const navigate = useNavigate();
  const { context } = useAuth();
  const { data: group, isPending, isError, error, refetch } = useCurrentGroup();
  const mutation = useUpdateGroupWeights();

  const [values, setValues] = useState<Record<number, number>>({});

  const initial = useMemo(
    () =>
      group
        ? Object.fromEntries(
            group.members.map((m) => [m.user_id, Math.round(Number.parseFloat(m.weight_percent) || 0)]),
          )
        : {},
    [group?.id], // eslint-disable-line react-hooks/exhaustive-deps
  );

  useEffect(() => {
    setValues(initial);
  }, [initial]);

  const total = useMemo(
    () => Object.values(values).reduce((acc, v) => acc + v, 0),
    [values],
  );

  if (isPending) return <Loader title="Загружаем участников…" />;
  if (isError) {
    return (
      <ErrorState
        title="Не удалось загрузить"
        description={error.message}
        accent="rgba(217,118,124"
        onRetry={() => void refetch()}
      />
    );
  }
  if (group === null) return <Navigate to={routes.onboarding} replace />;

  const isOwner = context?.user?.id === group.owner_user_id;
  if (!isOwner) return <Navigate to={routes.group} replace />;

  const sumIsValid = total === 100;

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    if (!sumIsValid) return;
    mutation.mutate(
      {
        weights: group.members.map((member) => ({
          user_id: member.user_id,
          weight_percent: String(values[member.user_id] ?? 0),
        })),
      },
      { onSuccess: () => navigate(routes.group) },
    );
  };

  const memberIds = group.members.map((m) => m.user_id);
  const setOne = (userId: number, value: number): void =>
    setValues((prev) => redistribute(prev, userId, value, memberIds));

  return (
    <Screen>
      <ScreenHeader title="Нагрузка участников" onBack={() => navigate(routes.group)} />
      <form onSubmit={handleSubmit} className="uk-stack" style={{ flex: 1 }}>
        <div style={{ font: "400 13px/1.5 'Manrope'", color: 'var(--uk-ink-70)' }}>
          Вес — это доля плановой нагрузки участника. Сумма всех долей должна быть 100%.
        </div>

        {/* Sum bar */}
        <div
          style={{
            padding: 16,
            borderRadius: 20,
            background: sumIsValid ? 'rgba(111,182,156,.08)' : 'rgba(217,118,124,.08)',
            border: `1px solid ${sumIsValid ? 'rgba(111,182,156,.24)' : 'rgba(217,118,124,.3)'}`,
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'baseline',
              marginBottom: 10,
            }}
          >
            <span style={{ font: "600 13px 'Manrope'", color: 'var(--uk-ink-70)' }}>Сумма</span>
            <span
              style={{
                font: "800 20px 'Manrope'",
                color: sumIsValid ? 'var(--uk-teal)' : 'var(--uk-danger)',
              }}
            >
              {total}%
            </span>
          </div>
          <div className="uk-stackbar">
            {group.members.map((m) => (
              <div
                key={m.user_id}
                style={{
                  width: `${values[m.user_id] ?? 0}%`,
                  background: avatarColor(m.user_id),
                  transition: 'width 0.12s ease',
                }}
              />
            ))}
          </div>
        </div>

        {/* Sliders */}
        <div className="uk-stack" style={{ gap: 16 }}>
          {group.members.map((member) => {
            const value = values[member.user_id] ?? 0;
            return (
              <div key={member.user_id} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ font: "600 15px 'Manrope'" }}>
                    {memberName(member)}
                    {member.user_id === context?.user?.id ? (
                      <span style={{ font: "500 12px 'Manrope'", color: 'var(--uk-ink-55)' }}>
                        {' '}
                        (вы)
                      </span>
                    ) : null}
                  </span>
                  <span style={{ font: "800 16px 'Manrope'", color: 'var(--uk-blue)' }}>{value}%</span>
                </div>
                <div className="uk-slider">
                  <input
                    className="uk-slider__input"
                    type="range"
                    min={0}
                    max={100}
                    step={1}
                    value={value}
                    disabled={mutation.isPending}
                    onChange={(e) => setOne(member.user_id, Number(e.currentTarget.value))}
                    aria-label={`Нагрузка: ${memberName(member)}`}
                  />
                  <div className="uk-slider__track">
                    <div
                      className="uk-slider__fill"
                      style={{ width: `${value}%`, background: avatarColor(member.user_id) }}
                    />
                  </div>
                  <div className="uk-slider__thumb" style={{ left: `${value}%` }} />
                </div>
              </div>
            );
          })}
        </div>

        <div style={{ display: 'flex', gap: 10, marginTop: 2 }}>
          <button
            type="button"
            className="uk-btn uk-btn--ghost"
            style={{
              flex: 1,
              padding: 12,
              borderColor: 'rgba(124,166,217,.3)',
              color: 'var(--uk-blue)',
              background: 'rgba(124,166,217,.08)',
              fontSize: 13,
              borderRadius: 14,
            }}
            disabled={mutation.isPending}
            onClick={() => setValues(evenSplit(group.members.map((m) => m.user_id)))}
          >
            Поровну
          </button>
          <button
            type="button"
            className="uk-btn uk-btn--ghost"
            style={{ flex: 1, padding: 12, fontSize: 13, borderRadius: 14 }}
            disabled={mutation.isPending}
            onClick={() => setValues(initial)}
          >
            Сбросить
          </button>
        </div>

        {!sumIsValid ? (
          <Note tone="error">Сумма долей должна быть ровно 100%, сейчас {total}%.</Note>
        ) : null}
        {mutation.isError ? <Note tone="error">{mutation.error.message}</Note> : null}

        <div className="uk-spacer" />
        <Button
          type="submit"
          variant="primary"
          loading={mutation.isPending}
          disabled={!sumIsValid}
        >
          Сохранить нагрузку
        </Button>
      </form>
    </Screen>
  );
}
