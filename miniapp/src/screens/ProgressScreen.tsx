import { Navigate } from '@/routes/navigation';

import { useCurrentGroup, useSprintResults } from '@/api/queries';
import { useAuth } from '@/auth/useAuth';
import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';
import { Card, Screen, ScreenHeader } from '@/components/ui/app-kit';
import { routes } from '@/routes/paths';
import { UNIT_SYMBOL, formatPeriod, formatUnits, memberName } from '@/ui/format';
import type { CompletedTaskBreakdownResponse } from '@/api/types';

/** Russian pluralisation for "раз / раза / раз". */
function pluralTimes(n: number): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return `${n} раза`;
  return `${n} раз`;
}

function byLatestCompletion(
  left: CompletedTaskBreakdownResponse,
  right: CompletedTaskBreakdownResponse,
): number {
  return Date.parse(right.last_completed_at) - Date.parse(left.last_completed_at);
}

function CompletionBreakdown({
  items,
  myUserId,
  emptyText,
}: {
  items: CompletedTaskBreakdownResponse[];
  myUserId: number | undefined;
  emptyText: string;
}) {
  if (items.length === 0) {
    return (
      <Card style={{ padding: 20, borderRadius: 20, textAlign: 'center' }}>
        <div style={{ font: "500 13px 'Manrope'", color: 'var(--uk-ink-55)' }}>{emptyText}</div>
      </Card>
    );
  }

  return (
    <Card flush>
      {items.map((item) => {
        const isMine = item.performer_user_id === myUserId;
        const who = memberName({
          first_name: item.performer_first_name,
          username: item.performer_username,
          user_id: item.performer_user_id,
        });
        return (
          <div className="uk-row" key={`${item.task_id}-${item.performer_user_id}`}>
            <div className="uk-row__grow">
              <div style={{ font: "600 15px 'Manrope'" }}>{item.title}</div>
              <div style={{ font: "400 12px 'Manrope'", color: 'var(--uk-ink-55)' }}>
                {isMine
                  ? pluralTimes(item.completed_count)
                  : `${who} · ${pluralTimes(item.completed_count)}`}
              </div>
            </div>
            <span style={{ font: "700 15px 'Manrope'", color: 'var(--uk-teal)' }}>
              {formatUnits(item.completed_units)} {UNIT_SYMBOL}
            </span>
          </div>
        );
      })}
    </Card>
  );
}

/**
 * Progress section. Shows how far the group has come this sprint — the share of
 * planned units completed, plus a per-task breakdown of what was done.
 */
export function ProgressScreen() {
  const { context } = useAuth();
  const myUserId = context?.user?.id;
  const group = useCurrentGroup();
  const { data, isPending, isError, error, refetch } = useSprintResults();

  if (group.data === null) return <Navigate to={routes.onboarding} replace />;
  if (isPending) return <Loader title="Считаем прогресс…" />;
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

  const pct = Math.max(0, Math.min(100, Math.round(Number.parseFloat(data.progress_percent) || 0)));
  const groupPct = Math.max(
    0,
    Math.min(100, Math.round(Number.parseFloat(data.group.progress_percent) || 0)),
  );
  const myBreakdown = data.breakdown
    .filter((item) => item.performer_user_id === myUserId)
    .sort(byLatestCompletion);
  const othersBreakdown = data.breakdown
    .filter((item) => item.performer_user_id !== myUserId)
    .sort(byLatestCompletion);

  return (
    <Screen>
      <ScreenHeader title="Прогресс" />

      {/* Headline progress */}
      <Card style={{ padding: 20, borderRadius: 24 }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 12,
          }}
        >
          <div className="uk-eyebrow" style={{ letterSpacing: '0.08em' }}>
            Спринт · {formatPeriod(data.period_start, data.period_end)}
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'baseline',
              gap: 5,
              padding: '4px 10px',
              borderRadius: 999,
              background: 'var(--uk-accent-soft)',
              whiteSpace: 'nowrap',
            }}
          >
            <span style={{ font: "700 13px 'Manrope'", color: 'var(--uk-accent)' }}>
              Группа {groupPct}%
            </span>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, margin: '10px 0 14px' }}>
          <span style={{ font: "800 40px/1 'Manrope'", color: 'var(--uk-teal)' }}>{pct}%</span>
          <span style={{ font: "500 13px 'Manrope'", color: 'var(--uk-ink-55)' }}>
            плана выполнено
          </span>
        </div>

        <div className="uk-progress" style={{ position: 'relative' }}>
          <div className="uk-progress__fill" style={{ width: `${pct}%` }} />
          <div
            title={`Группа: ${groupPct}%`}
            style={{
              position: 'absolute',
              top: -3,
              left: `calc(${groupPct}% - 1px)`,
              width: 2,
              height: 16,
              borderRadius: 1,
              background: '#fff',
              boxShadow: '0 0 0 1px var(--uk-accent)',
            }}
          />
        </div>

        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: 10,
            font: "600 13px 'Manrope'",
            color: 'var(--uk-ink-70)',
          }}
        >
          <span>
            Выполнено {formatUnits(data.completed_units)} {UNIT_SYMBOL}
          </span>
          <span>
            План {formatUnits(data.planned_units)} {UNIT_SYMBOL}
          </span>
        </div>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: 4,
            font: "500 12px 'Manrope'",
            color: 'var(--uk-ink-55)',
          }}
        >
          <span>
            Группа: выполнено {formatUnits(data.group.completed_units)} {UNIT_SYMBOL}
          </span>
          <span>
            план {formatUnits(data.group.planned_units)} {UNIT_SYMBOL}
          </span>
        </div>
      </Card>

      <section className="uk-stack">
        <div className="uk-eyebrow">Сделано вами</div>
        <CompletionBreakdown
          items={myBreakdown}
          myUserId={myUserId}
          emptyText="Вы пока ничего не выполнили в этом спринте."
        />
      </section>

      <section className="uk-stack">
        <div className="uk-eyebrow">Сделано другими участниками группы</div>
        <CompletionBreakdown
          items={othersBreakdown}
          myUserId={myUserId}
          emptyText="Другие участники пока ничего не выполнили в этом спринте."
        />
      </section>
    </Screen>
  );
}
