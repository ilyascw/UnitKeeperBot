import { useState } from 'react';
import { Navigate, useNavigate } from '@/routes/navigation';

import { useLeaveGroup } from '@/api/mutations';
import { useCurrentGroup } from '@/api/queries';
import { useAuth } from '@/auth/useAuth';
import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';
import { Avatar, BottomSheet, Button, Card, Note, Screen } from '@/components/ui/app-kit';
import { Button as UiButton } from '@/components/ui/button';
import { ScreenHeader as UiScreenHeader } from '@/components/ui/screen';
import { routes } from '@/routes/paths';
import {
  WEEKDAY_EVERY,
  balanceColor,
  daysLeftLabel,
  daysUntil,
  formatBalance,
  formatPeriod,
  memberName,
  pluralDays,
  pluralMembers,
} from '@/ui/format';
import {
  CalendarIcon,
  CheckIcon,
  ChevronIcon,
  CopyIcon,
  ErrorIcon,
  LeaveIcon,
  SettingsIcon,
  SlidersIcon,
} from '@/ui/icons';
import type { MemberCardResponse, Weekday } from '@/api/types';

/**
 * Main group surface. Leads with the two balances people check daily, then the
 * sprint window, the member roster, and — for owners — the join code and
 * management entries. Leaving is a deliberate action behind a confirmation
 * sheet rather than a prominent button.
 */
export function GroupScreen() {
  const navigate = useNavigate();
  const { context } = useAuth();
  const { data: group, isPending, isError, error, refetch } = useCurrentGroup();
  const leave = useLeaveGroup();
  const [confirmingLeave, setConfirmingLeave] = useState(false);
  const [copied, setCopied] = useState(false);

  if (isPending) return <Loader title="Загружаем группу…" />;
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

  const myUserId = context?.user?.id;
  const isOwner = myUserId === group.owner_user_id;
  const me = group.members.find((m) => m.user_id === myUserId);
  const otherMembers = group.members.filter((m) => m.user_id !== myUserId);
  // Backend transfers ownership to the active member with the lowest user_id
  // when the owner leaves; mirror that here so the warning matches reality.
  const handoverTo: MemberCardResponse | null =
    isOwner && otherMembers.length > 0
      ? [...otherMembers].sort((a, b) => a.user_id - b.user_id)[0]
      : null;

  const remaining = daysUntil(group.sprint_ends_at);

  const copyCode = async (): Promise<void> => {
    if (!group.join_secret) return;
    try {
      await navigator.clipboard.writeText(group.join_secret);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard blocked — the code is visible to copy manually */
    }
  };

  const onConfirmLeave = (): void => {
    leave.mutate(undefined, { onSuccess: () => navigate(routes.onboarding, { replace: true }) });
  };

  return (
    <Screen>
      <UiScreenHeader
        title={group.name}
        description={`${pluralMembers(group.members.length)} · вы ${isOwner ? 'владелец' : 'участник'}`}
      />

      {/* Balances */}
      <div style={{ display: 'flex', gap: 12 }}>
        <Card style={{ flex: 1, padding: 16, borderRadius: 20 }}>
          <div className="uk-eyebrow" style={{ letterSpacing: '0.06em' }}>
            Ваш баланс
          </div>
          <div
            style={{
              font: "800 26px 'Manrope'",
              marginTop: 6,
              color: me ? balanceColor(me.balance) : 'var(--uk-ink)',
            }}
          >
            {me ? formatBalance(me.balance) : '—'}
          </div>
        </Card>
        <Card style={{ flex: 1, padding: 16, borderRadius: 20 }}>
          <div className="uk-eyebrow" style={{ letterSpacing: '0.06em' }}>
            Баланс группы
          </div>
          <div style={{ font: "800 26px 'Manrope'", marginTop: 6 }}>
            {formatBalance(group.group_balance)}
          </div>
        </Card>
      </div>

      {/* Sprint */}
      <Card style={{ padding: 16, borderRadius: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div
            style={{
              width: 42,
              height: 42,
              flex: 'none',
              borderRadius: 13,
              display: 'grid',
              placeItems: 'center',
              background: 'rgba(124,166,217,.14)',
            }}
          >
            <CalendarIcon size={22} style={{ color: 'var(--uk-blue)' }} />
          </div>
          <div>
            <div style={{ font: "600 15px 'Manrope'" }}>
              Спринт: {formatPeriod(group.sprint_period_start, group.sprint_period_end)}
            </div>
            <div style={{ font: "400 12.5px 'Manrope'", color: 'var(--uk-ink-70)' }}>
              {pluralDays(group.sprint_duration_days)} · старт{' '}
              {WEEKDAY_EVERY[group.sprint_start_weekday as Weekday] ?? group.sprint_start_weekday} ·{' '}
              {daysLeftLabel(remaining)}
            </div>
          </div>
        </div>
      </Card>

      {/* Join code (owner) */}
      {isOwner && group.join_secret ? (
        <Card style={{ padding: 16, borderRadius: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div className="uk-row__grow">
              <div className="uk-eyebrow" style={{ letterSpacing: '0.06em' }}>
                Код вступления
              </div>
              <div style={{ font: "700 18px 'Manrope'", letterSpacing: '0.12em', marginTop: 4 }}>
                {group.join_secret}
              </div>
            </div>
            <UiButton type="button" size="sm" onClick={() => void copyCode()}>
              {copied ? <CheckIcon size={16} strokeWidth={2.6} /> : <CopyIcon size={16} />}
              {copied ? 'Скопировано' : 'Копировать'}
            </UiButton>
          </div>
        </Card>
      ) : null}

      {/* Members */}
      <div className="uk-eyebrow">Участники · {group.members.length}</div>
      <Card flush>
        {group.members.map((member) => {
          const you = member.user_id === myUserId;
          return (
            <div className="uk-row" key={member.user_id}>
              <Avatar label={memberName(member)} seed={member.user_id} />
              <div className="uk-row__grow">
                <div
                  style={{
                    font: "600 15px 'Manrope'",
                    display: 'flex',
                    gap: 6,
                    alignItems: 'center',
                  }}
                >
                  {memberName(member)}
                  {you ? (
                    <span style={{ font: "500 12px 'Manrope'", color: 'var(--uk-ink-55)' }}>
                      (вы)
                    </span>
                  ) : null}
                  {member.is_owner ? <span className="uk-badge">владелец</span> : null}
                </div>
                <div style={{ font: "400 12px 'Manrope'", color: 'var(--uk-ink-55)' }}>
                  Нагрузка {member.weight_percent}%
                </div>
              </div>
              <span style={{ font: "700 15px 'Manrope'", color: balanceColor(member.balance) }}>
                {formatBalance(member.balance)}
              </span>
            </div>
          );
        })}
      </Card>

      {/* Owner management */}
      {isOwner ? (
        <>
          <div className="uk-eyebrow">Управление группой</div>
          <Card flush>
            <UiButton
              type="button"
              variant="ghost"
              className="uk-row uk-row--tap"
              style={{ width: '100%', background: 'transparent', border: 'none', color: 'inherit' }}
              onClick={() => navigate(routes.groupSettings)}
            >
              <SettingsIcon size={20} style={{ color: 'var(--uk-blue)' }} />
              <span
                className="uk-row__grow"
                style={{ font: "600 15px 'Manrope'", textAlign: 'left' }}
              >
                Настройки группы
              </span>
              <ChevronIcon size={18} style={{ color: 'var(--uk-ink-45)' }} />
            </UiButton>
            <UiButton
              type="button"
              variant="ghost"
              className="uk-row uk-row--tap"
              style={{ width: '100%', background: 'transparent', border: 'none', color: 'inherit' }}
              onClick={() => navigate(routes.groupWeights)}
            >
              <SlidersIcon size={20} style={{ color: 'var(--uk-blue)' }} />
              <span
                className="uk-row__grow"
                style={{ font: "600 15px 'Manrope'", textAlign: 'left' }}
              >
                Нагрузка участников
              </span>
              <ChevronIcon size={18} style={{ color: 'var(--uk-ink-45)' }} />
            </UiButton>
          </Card>
        </>
      ) : null}

      <div style={{ textAlign: 'center', marginTop: 6 }}>
        <UiButton
          type="button"
          variant="link"
          className="uk-link-muted h-auto"
          onClick={() => setConfirmingLeave(true)}
        >
          Выйти из группы
        </UiButton>
      </div>

      {confirmingLeave ? (
        <BottomSheet onClose={() => (leave.isPending ? undefined : setConfirmingLeave(false))}>
          <div
            style={{
              width: 66,
              height: 66,
              borderRadius: 20,
              margin: '0 auto 18px',
              display: 'grid',
              placeItems: 'center',
              background: 'rgba(217,118,124,.14)',
              border: '1px solid rgba(217,118,124,.35)',
            }}
          >
            <LeaveIcon size={30} style={{ color: 'var(--uk-danger)' }} />
          </div>
          <div style={{ textAlign: 'center', font: "800 22px 'Manrope'", marginBottom: 12 }}>
            Выйти из группы?
          </div>
          <div
            style={{
              font: "400 14px/1.6 'Manrope'",
              color: 'var(--uk-ink-70)',
              textAlign: 'center',
              marginBottom: 20,
            }}
          >
            {handoverTo ? (
              <>
                Вы владелец. Владение перейдёт участнику{' '}
                <strong style={{ color: 'var(--uk-ink)' }}>{memberName(handoverTo)}</strong>.
              </>
            ) : isOwner ? (
              <>Вы владелец и последний участник. При выходе группа будет удалена.</>
            ) : (
              <>Вы потеряете доступ к группе.</>
            )}
          </div>

          <div className="uk-stack" style={{ gap: 10, marginBottom: 20 }}>
            <div
              style={{
                display: 'flex',
                gap: 10,
                alignItems: 'flex-start',
                padding: '13px 14px',
                borderRadius: 14,
                background: 'rgba(255,255,255,.05)',
              }}
            >
              <CheckIcon
                size={17}
                style={{ color: 'var(--uk-blue)', flex: 'none', marginTop: 1 }}
              />
              <span style={{ font: "400 13px/1.5 'Manrope'", color: 'var(--uk-ink-70)' }}>
                Ваши прошлые балансы и история сохранятся в группе
              </span>
            </div>
            <div
              style={{
                display: 'flex',
                gap: 10,
                alignItems: 'flex-start',
                padding: '13px 14px',
                borderRadius: 14,
                background: 'rgba(255,255,255,.05)',
              }}
            >
              <ErrorIcon
                size={17}
                style={{ color: 'var(--uk-warn)', flex: 'none', marginTop: 1 }}
              />
              <span style={{ font: "400 13px/1.5 'Manrope'", color: 'var(--uk-ink-70)' }}>
                Вернуться получится только по коду вступления
              </span>
            </div>
          </div>

          {leave.isError ? (
            <div style={{ marginBottom: 12 }}>
              <Note tone="error">{leave.error.message}</Note>
            </div>
          ) : null}

          <Button
            variant="danger"
            loading={leave.isPending}
            onClick={onConfirmLeave}
            style={{ marginBottom: 10 }}
          >
            {handoverTo ? 'Выйти и передать владение' : 'Выйти из группы'}
          </Button>
          <Button
            variant="soft"
            disabled={leave.isPending}
            onClick={() => setConfirmingLeave(false)}
          >
            Остаться
          </Button>
        </BottomSheet>
      ) : null}
    </Screen>
  );
}
