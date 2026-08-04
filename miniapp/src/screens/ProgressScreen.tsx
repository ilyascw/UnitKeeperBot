import { Navigate } from '@/routes/navigation';

import { useCurrentGroup, useSprintResults } from '@/api/queries';
import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';
import { Card, Screen, ScreenHeader } from '@/components/ui/app-kit';
import { routes } from '@/routes/paths';
import { UNIT_SYMBOL, formatPeriod, formatUnits } from '@/ui/format';

/** Russian pluralisation for "раз / раза / раз". */
function pluralTimes(n: number): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return `${n} раза`;
  return `${n} раз`;
}

/**
 * Progress section. Shows how far the group has come this sprint — the share of
 * planned units completed, plus a per-task breakdown of what was done.
 */
export function ProgressScreen() {
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

  return (
    <Screen>
      <ScreenHeader title="Прогресс" />

      {/* Headline progress */}
      <Card style={{ padding: 20, borderRadius: 24 }}>
        <div className="uk-eyebrow" style={{ letterSpacing: '0.08em' }}>
          Спринт · {formatPeriod(data.period_start, data.period_end)}
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, margin: '10px 0 14px' }}>
          <span style={{ font: "800 40px/1 'Manrope'", color: 'var(--uk-teal)' }}>{pct}%</span>
          <span style={{ font: "500 13px 'Manrope'", color: 'var(--uk-ink-55)' }}>
            плана выполнено
          </span>
        </div>
        <div className="uk-progress">
          <div className="uk-progress__fill" style={{ width: `${pct}%` }} />
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
      </Card>

      {/* Per-task breakdown */}
      <div className="uk-eyebrow">Что сделано</div>
      {data.breakdown.length === 0 ? (
        <Card style={{ padding: 20, borderRadius: 20, textAlign: 'center' }}>
          <div style={{ font: "600 15px 'Manrope'" }}>Пока ничего не выполнено</div>
          <div style={{ font: "400 13px 'Manrope'", color: 'var(--uk-ink-55)', marginTop: 6 }}>
            Отметьте задачи в разделе «Задачи», и они появятся здесь.
          </div>
        </Card>
      ) : (
        <Card flush>
          {data.breakdown.map((item) => (
            <div className="uk-row" key={item.task_id}>
              <div className="uk-row__grow">
                <div style={{ font: "600 15px 'Manrope'" }}>{item.title}</div>
                <div style={{ font: "400 12px 'Manrope'", color: 'var(--uk-ink-55)' }}>
                  {pluralTimes(item.completed_count)}
                </div>
              </div>
              <span style={{ font: "700 15px 'Manrope'", color: 'var(--uk-teal)' }}>
                {formatUnits(item.completed_units)} {UNIT_SYMBOL}
              </span>
            </div>
          ))}
        </Card>
      )}
    </Screen>
  );
}
