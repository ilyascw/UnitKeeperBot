import { useState } from 'react';
import { Navigate, useNavigate } from '@/routes/navigation';

import { useBalanceTransactions, useCurrentGroup } from '@/api/queries';
import { useAuth } from '@/auth/useAuth';
import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';
import { routes } from '@/routes/paths';
import { UNIT_SYMBOL, balanceColor, formatBalance, memberName } from '@/ui/format';
import {
  Avatar,
  Button,
  Card,
  Note,
  Screen,
  ScreenHeader,
  Segmented,
} from '@/components/ui/app-kit';

const TRANSACTION_LABELS: Record<string, string> = {
  transfer: 'Перевод',
  sprint_settlement: 'Спринт-расчёт',
  manual_adjustment: 'Ручная корректировка',
};

const HISTORY_PAGE_SIZE = 20;

/**
 * Balance section. Leads with the member's own balance, then ranks the group so
 * everyone can see who is ahead of or behind their share of the load.
 */
export function BalanceScreen() {
  const navigate = useNavigate();
  const { context } = useAuth();
  const { data: group, isPending, isError, error, refetch } = useCurrentGroup();
  const [tab, setTab] = useState<'overview' | 'history'>('overview');
  const [historyLimit, setHistoryLimit] = useState(HISTORY_PAGE_SIZE);
  const {
    data: history,
    isPending: historyPending,
    isError: historyIsError,
    error: historyError,
  } = useBalanceTransactions({ limit: historyLimit, offset: 0 }, tab === 'history');

  if (isPending) return <Loader title="Загружаем баланс…" />;
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
  const me = group.members.find((m) => m.user_id === myUserId);
  const myBalance = me?.balance ?? '0';
  const negative = Number.parseFloat(myBalance) < 0;

  const ranked = [...group.members].sort(
    (a, b) => Number.parseFloat(b.balance) - Number.parseFloat(a.balance),
  );
  const membersById = new Map(group.members.map((m) => [m.user_id, m]));

  return (
    <Screen>
      <ScreenHeader title="Баланс" />

      {/* My balance hero */}
      <div
        style={{
          padding: 22,
          borderRadius: 26,
          background: negative ? 'rgba(217,118,124,.14)' : 'var(--uk-accent-soft)',
          border: `1px solid ${negative ? 'rgba(217,118,124,.28)' : 'rgba(124,166,217,.28)'}`,
          boxShadow: 'inset 0 1px 0 rgba(255,255,255,.16),0 20px 40px -18px rgba(0,0,0,.5)',
        }}
      >
        <div className="uk-eyebrow" style={{ letterSpacing: '0.08em' }}>
          Ваш баланс
        </div>
        <div
          style={{ font: "800 42px/1 'Manrope'", marginTop: 10, color: balanceColor(myBalance) }}
        >
          {formatBalance(myBalance)}{' '}
          <span style={{ font: "600 18px 'Manrope'", color: 'var(--uk-ink-55)' }}>
            {UNIT_SYMBOL}
          </span>
        </div>
      </div>

      <Button variant="primary" onClick={() => navigate(routes.balanceTransfer)}>
        Перевести юниты
      </Button>

      <Segmented
        options={[
          { value: 'overview', label: 'Обзор' },
          { value: 'history', label: 'История' },
        ]}
        value={tab}
        onChange={setTab}
      />

      {tab === 'overview' ? (
        <>
          {/* Group total */}
          <Card
            style={{
              padding: 16,
              borderRadius: 20,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span style={{ font: "600 14px 'Manrope'", color: 'var(--uk-ink-70)' }}>
              Баланс группы
            </span>
            <span style={{ font: "800 20px 'Manrope'", color: balanceColor(group.group_balance) }}>
              {formatBalance(group.group_balance)} {UNIT_SYMBOL}
            </span>
          </Card>

          {/* Ranked members */}
          <div className="uk-eyebrow">Участники</div>
          <Card flush>
            {ranked.map((member) => {
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

          <Note tone="info">
            Баланс — это вклад относительно вашей доли нагрузки. Плюс — вы сделали больше нормы,
            минус — меньше.
          </Note>
        </>
      ) : (
        <>
          {historyPending ? <Loader title="Загружаем историю…" /> : null}
          {historyIsError ? <Note tone="error">{historyError.message}</Note> : null}
          {history ? (
            <>
              {history.items.length === 0 ? (
                <Note tone="info">Пока нет операций.</Note>
              ) : (
                <Card flush>
                  {history.items.map((tx) => {
                    const positive = Number.parseFloat(tx.amount_delta) >= 0;
                    const counterparty =
                      tx.counterparty_user_id != null
                        ? membersById.get(tx.counterparty_user_id)
                        : undefined;
                    let label = TRANSACTION_LABELS[tx.transaction_type] ?? tx.transaction_type;
                    if (tx.transaction_type === 'transfer') {
                      const who = counterparty
                        ? memberName(counterparty)
                        : `Участник ${tx.counterparty_user_id}`;
                      label = positive ? `Перевод · от ${who}` : `Перевод · ${who}`;
                    } else if (tx.transaction_type === 'manual_adjustment' && tx.description) {
                      label = `${label} · ${tx.description}`;
                    }
                    return (
                      <div className="uk-row" key={tx.id}>
                        <div className="uk-row__grow">
                          <div style={{ font: "600 14px 'Manrope'" }}>{label}</div>
                          <div style={{ font: "400 11.5px 'Manrope'", color: 'var(--uk-ink-55)' }}>
                            {new Date(tx.created_at).toLocaleString('ru-RU', {
                              day: 'numeric',
                              month: 'long',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </div>
                        </div>
                        <span
                          style={{
                            font: "700 15px 'Manrope'",
                            color: positive ? 'var(--uk-positive)' : 'var(--uk-danger-soft)',
                          }}
                        >
                          {formatBalance(tx.amount_delta)}
                        </span>
                      </div>
                    );
                  })}
                </Card>
              )}
              {history.has_more ? (
                <Button
                  variant="ghost"
                  onClick={() => setHistoryLimit((limit) => limit + HISTORY_PAGE_SIZE)}
                >
                  Показать ещё
                </Button>
              ) : null}
            </>
          ) : null}
        </>
      )}
    </Screen>
  );
}
