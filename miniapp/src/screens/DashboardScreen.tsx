import { useEffect, useState } from 'react';
import { Navigate, useNavigate } from '@/routes/navigation';

import { useMarkTaskDone } from '@/api/mutations';
import { useCurrentGroup, usePendingApprovals, useSprintResults, useTasks } from '@/api/queries';
import type { TaskLogViewResponse, TaskResponse } from '@/api/types';
import { useAuth } from '@/auth/useAuth';
import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';
import { LogRow, RejectSheet } from '@/components/TaskLogRow';
import { Card, Screen, Toast } from '@/components/ui/app-kit';
import { Button as UiButton } from '@/components/ui/button';
import { ScreenHeader as UiScreenHeader } from '@/components/ui/screen';
import { Spinner } from '@/components/ui/spinner';
import { routes } from '@/routes/paths';
import {
  UNIT_SYMBOL,
  balanceColor,
  daysLeftLabel,
  daysUntil,
  formatBalance,
  formatUnits,
  pluralMembers,
} from '@/ui/format';
import { ChevronIcon, ClockIcon } from '@/ui/icons';

/** Task is on hold this sprint (no slots planned). */
function taskIsPaused(task: TaskResponse): boolean {
  return task.frequency_per_sprint === 0;
}

/** Task has at least one free slot a member can claim right now. */
function taskIsMarkable(task: TaskResponse): boolean {
  return task.available_in_sprint > 0;
}

/** Every remaining slot is already held by a pending, unconfirmed log. */
function taskIsHeldFull(task: TaskResponse): boolean {
  return !taskIsPaused(task) && task.remaining_in_sprint > 0 && !taskIsMarkable(task);
}

/** A short, plain-language read on where a member's balance stands. */
function balanceCaption(value: string): string {
  const n = Number.parseFloat(value);
  if (!Number.isFinite(n) || n === 0) return 'Ровно по норме';
  if (n > 0) return '';
  if (n > -5) return 'Небольшой долг — почти в норме';
  return 'Есть долг по нагрузке';
}

/**
 * Home section. Surfaces the three things a member checks daily — their
 * balance, sprint progress, and what is left to do — each linking into its
 * dedicated section.
 */
export function DashboardScreen() {
  const navigate = useNavigate();
  const { context } = useAuth();
  const { data: group, isPending, isError, error, refetch } = useCurrentGroup();
  const results = useSprintResults();
  const tasksQuery = useTasks();
  const pendingApprovals = usePendingApprovals(true);
  const markDone = useMarkTaskDone();
  const [rejecting, setRejecting] = useState<TaskLogViewResponse | null>(null);
  const [toast, setToast] = useState<{ tone: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 2800);
    return () => clearTimeout(timer);
  }, [toast]);

  const handleMarkDone = (task: TaskResponse): void => {
    markDone.mutate(task.id, {
      onSuccess: (log) =>
        setToast({
          tone: 'success',
          text: log.status === 'pending' ? 'Отправлено на подтверждение' : 'Задача засчитана',
        }),
      onError: () => setToast({ tone: 'error', text: 'Не удалось отметить задачу' }),
    });
  };

  if (isPending) return <Loader title="Загружаем…" label="Открываем вашу группу." />;
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
  const myBalance = me?.balance ?? '0';
  const negative = Number.parseFloat(myBalance) < 0;
  const caption = balanceCaption(myBalance);

  const remaining = daysUntil(group.sprint_ends_at);
  const progress = results.data ? Number.parseFloat(results.data.progress_percent) : null;
  const progressPct = progress === null ? 0 : Math.max(0, Math.min(100, Math.round(progress)));
  const groupProgress = results.data ? Number.parseFloat(results.data.group.progress_percent) : null;
  const groupProgressPct =
    groupProgress === null ? 0 : Math.max(0, Math.min(100, Math.round(groupProgress)));

  const openTasks = (tasksQuery.data ?? [])
    .filter((t) => t.remaining_in_sprint > 0)
    .sort((a, b) => Number.parseFloat(b.unit_cost) - Number.parseFloat(a.unit_cost));
  const pendingItems = pendingApprovals.data?.items ?? [];

  return (
    <Screen>
      <UiScreenHeader
        title={group.name}
        description={`${pluralMembers(group.members.length)} · вы ${isOwner ? 'владелец' : 'участник'}`}
      />

      {/* Balance + sprint, side by side */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
          gap: 12,
        }}
      >
        {/* Balance hero */}
        <UiButton
          type="button"
          variant="ghost"
          className="h-auto min-w-0 w-full flex-col items-stretch justify-start gap-0 overflow-hidden whitespace-normal"
          onClick={() => navigate(routes.balance)}
          style={{
            textAlign: 'left',
            padding: 18,
            borderRadius: 22,
            cursor: 'pointer',
            background: negative ? 'rgba(217,118,124,.14)' : 'var(--uk-accent-soft)',
            border: `1px solid ${negative ? 'rgba(217,118,124,.28)' : 'rgba(124,166,217,.28)'}`,
            boxShadow: 'inset 0 1px 0 rgba(255,255,255,.16),0 20px 40px -18px rgba(0,0,0,.5)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="uk-eyebrow" style={{ letterSpacing: '0.08em' }}>
              Баланс
            </div>
            <ChevronIcon size={16} style={{ color: 'var(--uk-ink-45)' }} />
          </div>
          <div
            style={{
              font: "800 26px/1.2 'Manrope'",
              marginTop: 10,
              color: balanceColor(myBalance),
            }}
          >
            {formatBalance(myBalance)}{' '}
            <span style={{ font: "600 14px 'Manrope'", color: 'var(--uk-ink-55)' }}>
              {UNIT_SYMBOL}
            </span>
          </div>
          {caption ? (
            <div
              style={{
                font: "500 12px 'Manrope'",
                marginTop: 6,
                color: negative ? 'var(--uk-danger-soft)' : 'var(--uk-ink-70)',
              }}
            >
              {caption}
            </div>
          ) : null}
        </UiButton>

        {/* Sprint progress */}
        <UiButton
          type="button"
          variant="ghost"
          className="h-auto min-w-0 w-full flex-col items-stretch justify-start gap-0 overflow-hidden whitespace-normal"
          onClick={() => navigate(routes.progress)}
          style={{
            textAlign: 'left',
            padding: 18,
            borderRadius: 22,
            cursor: 'pointer',
            background: 'var(--uk-glass)',
            border: '1px solid var(--uk-hairline)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="uk-eyebrow" style={{ letterSpacing: '0.08em' }}>
              Спринт
            </div>
            <ChevronIcon size={16} style={{ color: 'var(--uk-ink-45)' }} />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 10 }}>
            <div style={{ font: "800 26px/1.2 'Manrope'" }}>
              {progress === null ? '…' : `${progressPct}%`}
            </div>
            {results.data ? (
              <span
                style={{
                  font: "700 11px 'Manrope'",
                  color: 'var(--uk-accent)',
                  background: 'var(--uk-accent-soft)',
                  padding: '3px 8px',
                  borderRadius: 999,
                  whiteSpace: 'nowrap',
                }}
              >
                Группа {groupProgressPct}%
              </span>
            ) : null}
          </div>
          <div className="uk-progress" style={{ marginTop: 10, position: 'relative' }}>
            <div className="uk-progress__fill" style={{ width: `${progressPct}%` }} />
            {results.data ? (
              <div
                title={`Группа: ${groupProgressPct}%`}
                style={{
                  position: 'absolute',
                  top: -3,
                  left: `calc(${groupProgressPct}% - 1px)`,
                  width: 2,
                  height: 16,
                  borderRadius: 1,
                  background: '#fff',
                  boxShadow: '0 0 0 1px var(--uk-accent)',
                }}
              />
            ) : null}
          </div>
          <div style={{ font: "500 12px 'Manrope'", marginTop: 8, color: 'var(--uk-ink-70)' }}>
            {daysLeftLabel(remaining)}
          </div>
        </UiButton>
      </div>

      {/* Pending approvals */}
      {pendingItems.length > 0 ? (
        <>
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
            <div className="uk-eyebrow">Ожидает подтверждения</div>
            <UiButton
              type="button"
              variant="link"
              size="sm"
              className="h-auto p-0"
              onClick={() => navigate(routes.taskLogs)}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--uk-blue)',
                font: "600 12px 'Manrope'",
              }}
            >
              все отметки
            </UiButton>
          </div>
          <Card flush>
            {pendingItems.map((log) => (
              <LogRow key={log.id} log={log} actions onReject={() => setRejecting(log)} />
            ))}
          </Card>
        </>
      ) : null}

      {/* Today tasks */}
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
        <div className="uk-eyebrow">Сделать в спринте</div>
        <UiButton
          type="button"
          variant="link"
          size="sm"
          className="h-auto p-0"
          onClick={() => navigate(routes.tasks)}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: 'var(--uk-blue)',
            font: "600 12px 'Manrope'",
          }}
        >
          все задачи
        </UiButton>
      </div>

      {tasksQuery.isError ? (
        <Card style={{ padding: 16, borderRadius: 18 }}>
          <div style={{ font: "400 13px 'Manrope'", color: 'var(--uk-ink-55)' }}>
            Не удалось загрузить задачи
          </div>
        </Card>
      ) : openTasks.length === 0 ? (
        <Card style={{ padding: 18, borderRadius: 18 }}>
          <div style={{ font: "600 14px 'Manrope'" }}>Всё сделано 🎉</div>
          <div style={{ font: "400 12.5px 'Manrope'", color: 'var(--uk-ink-55)', marginTop: 4 }}>
            На этот спринт задач не осталось.
          </div>
        </Card>
      ) : (
        <div className="uk-stack" style={{ gap: 10 }}>
          {openTasks.map((task) => {
            const heldFull = taskIsHeldFull(task);
            const markable = taskIsMarkable(task);
            const rowLoading = markDone.isPending && markDone.variables === task.id;
            const rowLocked = !markable || (markDone.isPending && !rowLoading);
            return (
              <div
                key={task.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 14,
                  padding: '15px 16px',
                  borderRadius: 18,
                  background: 'rgba(255,255,255,.05)',
                  border: '1px solid rgba(255,255,255,.09)',
                }}
              >
                <UiButton
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="shrink-0"
                  disabled={rowLocked}
                  onClick={(event) => {
                    event.stopPropagation();
                    handleMarkDone(task);
                  }}
                  aria-label={
                    heldFull ? 'Ждёт подтверждения' : `Отметить «${task.title}»`
                  }
                  style={{
                    width: 26,
                    height: 26,
                    flex: 'none',
                    borderRadius: 9,
                    display: 'grid',
                    placeItems: 'center',
                    padding: 0,
                    cursor: rowLocked ? 'default' : 'pointer',
                    background: 'transparent',
                    border: heldFull
                      ? '2px solid rgba(217,173,102,.6)'
                      : '2px solid rgba(124,166,217,.5)',
                    color: 'var(--uk-warn)',
                  }}
                >
                  {rowLoading ? (
                    <Spinner className="text-primary" aria-hidden="true" />
                  ) : heldFull ? (
                    <ClockIcon size={14} />
                  ) : null}
                </UiButton>
                <UiButton
                  type="button"
                  variant="ghost"
                  className="h-auto min-w-0 flex-1 flex-col items-start justify-start gap-0 whitespace-normal rounded-none"
                  onClick={() => navigate(routes.tasks)}
                  style={{
                    flex: 1,
                    minWidth: 0,
                    padding: 0,
                    border: 'none',
                    background: 'none',
                    color: 'inherit',
                    textAlign: 'left',
                    cursor: 'pointer',
                  }}
                  aria-label={`Открыть задачу «${task.title}»`}
                >
                  <div style={{ font: "600 15px 'Manrope'" }}>{task.title}</div>
                  <div style={{ font: "400 12px 'Manrope'", color: 'var(--uk-ink-55)' }}>
                    {task.completed_in_sprint} из {task.frequency_per_sprint} за спринт
                  </div>
                </UiButton>
                <span style={{ font: "700 14px 'Manrope'", color: 'var(--uk-teal)' }}>
                  {formatUnits(task.unit_cost)} {UNIT_SYMBOL}
                </span>
              </div>
            );
          })}
        </div>
      )}
      {rejecting ? <RejectSheet log={rejecting} onClose={() => setRejecting(null)} /> : null}
      {toast ? <Toast tone={toast.tone} message={toast.text} /> : null}
    </Screen>
  );
}
