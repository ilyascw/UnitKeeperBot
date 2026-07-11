import { Navigate } from 'react-router-dom';

import { useCurrentGroup } from '@/api/queries';
import { useAuth } from '@/auth/useAuth';
import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';
import { routes } from '@/routes/paths';
import { balanceColor, formatBalance, memberName } from '@/ui/format';
import { Avatar, Card, Note, Screen } from '@/ui/kit';

/**
 * Balance section. Leads with the member's own balance, then ranks the group so
 * everyone can see who is ahead of or behind their share of the load.
 */
export function BalanceScreen() {
  const { context } = useAuth();
  const { data: group, isPending, isError, error, refetch } = useCurrentGroup();

  if (isPending) return <Loader title="Загружаем баланс…" />;
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
  const me = group.members.find((m) => m.user_id === myUserId);
  const myBalance = me?.balance ?? '0';
  const negative = Number.parseFloat(myBalance) < 0;

  const ranked = [...group.members].sort(
    (a, b) => Number.parseFloat(b.balance) - Number.parseFloat(a.balance),
  );

  return (
    <Screen>
      <div className="uk-header">
        <div className="uk-header__title">Баланс</div>
      </div>

      {/* My balance hero */}
      <div
        style={{
          padding: 22,
          borderRadius: 26,
          background: negative
            ? 'linear-gradient(150deg,rgba(255,120,140,.2),rgba(90,120,255,.14))'
            : 'linear-gradient(150deg,rgba(61,215,196,.2),rgba(90,120,255,.14))',
          border: `1px solid ${negative ? 'rgba(255,120,140,.28)' : 'rgba(61,215,196,.28)'}`,
          boxShadow: 'inset 0 1px 0 rgba(255,255,255,.16),0 20px 40px -18px rgba(0,0,0,.5)',
        }}
      >
        <div className="uk-eyebrow" style={{ letterSpacing: '0.08em' }}>
          Ваш баланс
        </div>
        <div style={{ font: "800 42px/1 'Manrope'", marginTop: 10, color: balanceColor(myBalance) }}>
          {formatBalance(myBalance)}{' '}
          <span style={{ font: "600 18px 'Manrope'", color: 'var(--uk-ink-55)' }}>ю</span>
        </div>
      </div>

      {/* Group total */}
      <Card style={{ padding: 16, borderRadius: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ font: "600 14px 'Manrope'", color: 'var(--uk-ink-70)' }}>Баланс группы</span>
        <span style={{ font: "800 20px 'Manrope'", color: balanceColor(group.group_balance) }}>
          {formatBalance(group.group_balance)} ю
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
                    <span style={{ font: "500 12px 'Manrope'", color: 'var(--uk-ink-55)' }}>(вы)</span>
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
        Баланс — это вклад относительно вашей доли нагрузки. Плюс — вы сделали больше нормы, минус —
        меньше.
      </Note>
    </Screen>
  );
}
