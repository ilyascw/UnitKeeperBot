import { Navigate, useNavigate } from 'react-router-dom';

import { useCurrentGroup, useSprintResults, useTasks } from '@/api/queries';
import { useAuth } from '@/auth/useAuth';
import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';
import { routes } from '@/routes/paths';
import {
  balanceColor,
  daysUntil,
  formatBalance,
  formatPeriod,
  formatUnits,
  pluralDays,
  pluralMembers,
} from '@/ui/format';
import { Card, Screen } from '@/ui/kit';
import { ChevronIcon } from '@/ui/icons';

/** A short, plain-language read on where a member's balance stands. */
function balanceCaption(value: string): string {
  const n = Number.parseFloat(value);
  if (!Number.isFinite(n) || n === 0) return 'Ровно по норме';
  if (n > 0) return 'Вы сделали больше своей доли';
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

  if (isPending) return <Loader title="Загружаем…" label="Открываем вашу группу." />;
  if (isError) {
    return (
      <ErrorState
        title="Не удалось загрузить"
        description={error.message}
        accent="rgba(255,86,110"
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

  const remaining = daysUntil(group.sprint_ends_at);
  const progress = results.data ? Number.parseFloat(results.data.progress_percent) : null;
  const progressPct = progress === null ? 0 : Math.max(0, Math.min(100, Math.round(progress)));

  const openTasks = (tasksQuery.data ?? [])
    .filter((t) => t.remaining_in_sprint > 0)
    .slice(0, 3);

  return (
    <Screen>
      <div className="uk-header" style={{ justifyContent: 'space-between' }}>
        <div>
          <div style={{ font: "700 20px 'Manrope'" }}>{group.name}</div>
          <div style={{ font: "400 12.5px 'Manrope'", color: 'var(--uk-ink-55)' }}>
            {pluralMembers(group.members.length)} · вы {isOwner ? 'владелец' : 'участник'}
          </div>
        </div>
      </div>

      {/* Balance hero */}
      <button
        type="button"
        onClick={() => navigate(routes.balance)}
        style={{
          textAlign: 'left',
          padding: 22,
          borderRadius: 26,
          cursor: 'pointer',
          background: negative
            ? 'linear-gradient(150deg,rgba(255,120,140,.2),rgba(90,120,255,.14))'
            : 'linear-gradient(150deg,rgba(61,215,196,.2),rgba(90,120,255,.14))',
          border: `1px solid ${negative ? 'rgba(255,120,140,.28)' : 'rgba(61,215,196,.28)'}`,
          boxShadow: 'inset 0 1px 0 rgba(255,255,255,.16),0 20px 40px -18px rgba(0,0,0,.5)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="uk-eyebrow" style={{ letterSpacing: '0.08em' }}>
            Ваш баланс
          </div>
          <ChevronIcon size={18} style={{ color: 'var(--uk-ink-45)' }} />
        </div>
        <div
          style={{
            font: "800 42px/1 'Manrope'",
            marginTop: 10,
            color: balanceColor(myBalance),
          }}
        >
          {formatBalance(myBalance)}{' '}
          <span style={{ font: "600 18px 'Manrope'", color: 'var(--uk-ink-55)' }}>ю</span>
        </div>
        <div
          style={{
            font: "500 13px 'Manrope'",
            marginTop: 6,
            color: negative ? 'var(--uk-danger-soft)' : 'var(--uk-ink-70)',
          }}
        >
          {balanceCaption(myBalance)}
        </div>
      </button>

      {/* Sprint progress */}
      <Card style={{ padding: 18, borderRadius: 22 }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 12,
          }}
        >
          <div style={{ font: "700 15px 'Manrope'" }}>Спринт</div>
          <span
            style={{
              font: "600 12px 'Manrope'",
              color: 'var(--uk-on-accent)',
              padding: '5px 11px',
              borderRadius: 999,
              background: 'var(--uk-accent-grad)',
            }}
          >
            осталось {pluralDays(remaining)}
          </span>
        </div>
        <div style={{ font: "400 12.5px 'Manrope'", color: 'var(--uk-ink-70)', marginBottom: 10 }}>
          {formatPeriod(group.sprint_period_start, group.sprint_period_end)}
          {results.data
            ? ` · выполнено ${formatUnits(results.data.completed_units)} из ${formatUnits(results.data.planned_units)} ю`
            : ''}
        </div>
        <div className="uk-progress">
          <div className="uk-progress__fill" style={{ width: `${progressPct}%` }} />
        </div>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: 8,
            font: "600 12px 'Manrope'",
            color: 'var(--uk-ink-70)',
          }}
        >
          <span>{progress === null ? 'Считаем…' : `${progressPct}% плана`}</span>
          <button
            type="button"
            onClick={() => navigate(routes.progress)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--uk-blue)', font: "600 12px 'Manrope'" }}
          >
            Подробнее
          </button>
        </div>
      </Card>

      {/* Today tasks */}
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
        <div className="uk-eyebrow">Сделать в спринте</div>
        <button
          type="button"
          onClick={() => navigate(routes.tasks)}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--uk-blue)', font: "600 12px 'Manrope'" }}
        >
          все задачи
        </button>
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
          {openTasks.map((task) => (
            <button
              key={task.id}
              type="button"
              onClick={() => navigate(routes.tasks)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                padding: '15px 16px',
                borderRadius: 18,
                textAlign: 'left',
                cursor: 'pointer',
                background: 'rgba(255,255,255,.05)',
                border: '1px solid rgba(255,255,255,.09)',
              }}
            >
              <div
                style={{
                  width: 26,
                  height: 26,
                  flex: 'none',
                  borderRadius: 9,
                  border: '2px solid rgba(94,199,255,.5)',
                }}
              />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ font: "600 15px 'Manrope'" }}>{task.title}</div>
                <div style={{ font: "400 12px 'Manrope'", color: 'var(--uk-ink-55)' }}>
                  {task.completed_in_sprint} из {task.frequency_per_sprint} за спринт
                </div>
              </div>
              <span style={{ font: "700 14px 'Manrope'", color: 'var(--uk-teal)' }}>
                {formatUnits(task.unit_cost)} ю
              </span>
            </button>
          ))}
        </div>
      )}
    </Screen>
  );
}
