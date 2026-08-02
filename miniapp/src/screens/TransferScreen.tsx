import { useMemo, useState } from 'react';
import { Navigate, useNavigate } from '@/routes/navigation';

import { useCreateTransfer } from '@/api/mutations';
import { useCurrentGroup, useTransferCandidates } from '@/api/queries';
import { useAuth } from '@/auth/useAuth';
import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';
import { routes } from '@/routes/paths';
import type { UserResponse } from '@/api/types';
import { avatarColor } from '@/ui/avatar';
import { UNIT_SYMBOL, balanceColor, formatBalance, memberName } from '@/ui/format';
import { Avatar, Button, Note, Screen, ScreenHeader, TextInput } from '@/ui/kit';

type Step = 'recipient' | 'amount' | 'success';

function candidateName(user: UserResponse): string {
  return memberName({ user_id: user.id, first_name: user.first_name, username: user.username });
}

/** Owner-agnostic transfer flow: pick an active teammate, enter an amount up
 * to your current balance, confirm. Debt balances can't fund a transfer. */
export function TransferScreen() {
  const navigate = useNavigate();
  const { context } = useAuth();
  const { data: group, isPending: groupPending, isError: groupIsError, error: groupError, refetch: refetchGroup } =
    useCurrentGroup();
  const {
    data: candidates,
    isPending: candidatesPending,
    isError: candidatesIsError,
    error: candidatesError,
    refetch: refetchCandidates,
  } = useTransferCandidates();
  const mutation = useCreateTransfer();

  const [step, setStep] = useState<Step>('recipient');
  const [recipientId, setRecipientId] = useState<number | null>(null);
  const [amount, setAmount] = useState('');

  const myUserId = context?.user?.id;
  const myBalance = useMemo(() => {
    const me = group?.members.find((m) => m.user_id === myUserId);
    return me?.balance ?? '0';
  }, [group, myUserId]);
  const myBalanceNum = Number.parseFloat(myBalance);
  const canTransfer = Number.isFinite(myBalanceNum) && myBalanceNum > 0;

  if (groupPending || candidatesPending) return <Loader title="Загружаем…" />;
  if (groupIsError) {
    return (
      <ErrorState
        title="Не удалось загрузить"
        description={groupError.message}
        accent="rgba(217,118,124"
        onRetry={() => void refetchGroup()}
      />
    );
  }
  if (candidatesIsError) {
    return (
      <ErrorState
        title="Не удалось загрузить"
        description={candidatesError.message}
        accent="rgba(217,118,124"
        onRetry={() => void refetchCandidates()}
      />
    );
  }
  if (group === null) return <Navigate to={routes.onboarding} replace />;

  const recipient = candidates?.candidates.find((c) => c.user.id === recipientId) ?? null;

  const amountNum = Number.parseFloat(amount.replace(',', '.'));
  const amountIsValid = Number.isFinite(amountNum) && amountNum > 0 && amountNum <= myBalanceNum;
  const remaining = amountIsValid ? myBalanceNum - amountNum : myBalanceNum;

  const handleClose = () => navigate(routes.balance);

  const handleConfirm = () => {
    if (!recipient || !amountIsValid) return;
    mutation.mutate(
      { recipient_user_id: recipient.user.id, amount: amountNum.toFixed(2) },
      { onSuccess: () => setStep('success') },
    );
  };

  if (step === 'success' && recipient) {
    return (
      <Screen centered>
        <div className="uk-stack" style={{ alignItems: 'center', textAlign: 'center', gap: 20 }}>
          <div
            style={{
              width: 88,
              height: 88,
              borderRadius: 26,
              display: 'grid',
              placeItems: 'center',
              background: 'var(--uk-positive)',
              boxShadow: '0 10px 24px -8px rgba(0,0,0,.45),inset 0 1px 0 rgba(255,255,255,.5)',
            }}
          >
            <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="#06121a" strokeWidth={2.6} strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 6L9 17l-5-5" />
            </svg>
          </div>
          <div>
            <div style={{ font: "800 22px 'Manrope'", marginBottom: 8 }}>
              Переведено {amountNum.toFixed(2)} {UNIT_SYMBOL}
            </div>
            <div style={{ font: "400 15px/1.6 'Manrope'", color: 'var(--uk-ink-70)', maxWidth: 260 }}>
              {candidateName(recipient.user)} получил юниты. Ваш новый баланс —{' '}
              <span style={{ color: 'var(--uk-positive)', fontWeight: 600 }}>
                {formatBalance(mutation.data?.sender_balance ?? String(remaining))} {UNIT_SYMBOL}
              </span>
              .
            </div>
          </div>
          <Button variant="primary" onClick={handleClose} style={{ maxWidth: 260, width: '100%' }}>
            Готово
          </Button>
        </div>
      </Screen>
    );
  }

  if (step === 'amount' && recipient) {
    return (
      <Screen>
        <ScreenHeader title="Сумма перевода" onBack={() => setStep('recipient')} />
        <div className="uk-stack">
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 13,
              padding: '14px 16px',
              borderRadius: 18,
              background: 'var(--uk-glass)',
              border: '1px solid var(--uk-hairline)',
            }}
          >
            <span style={{ font: "400 12px 'Manrope'", color: 'var(--uk-ink-55)' }}>Получатель</span>
            <div style={{ flex: 1 }} />
            <Avatar label={candidateName(recipient.user)} seed={recipient.user.id} />
            <span style={{ font: "700 15px 'Manrope'" }}>{candidateName(recipient.user)}</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, padding: '20px 0 4px' }}>
            <div style={{ font: "600 11px 'Manrope'", letterSpacing: '.12em', textTransform: 'uppercase', color: 'var(--uk-ink-45)' }}>
              Сумма
            </div>
            <TextInput
              inputMode="decimal"
              placeholder="0.00"
              value={amount}
              onChange={(e) => setAmount(e.currentTarget.value)}
              style={{
                border: 'none',
                background: 'transparent',
                textAlign: 'center',
                font: "800 48px 'Manrope'",
                width: '100%',
                padding: 0,
              }}
            />
            <div style={{ font: "400 12.5px 'Manrope'", color: 'var(--uk-ink-55)' }}>
              Из {formatBalance(myBalance)} {UNIT_SYMBOL} · остаток:{' '}
              <span style={{ color: balanceColor(String(remaining)) }}>
                {formatBalance(String(remaining))} {UNIT_SYMBOL}
              </span>
            </div>
          </div>

          {!amountIsValid && amount.length > 0 ? (
            <Note tone="error">
              {amountNum > myBalanceNum
                ? 'Нельзя перевести больше, чем есть на балансе'
                : 'Введите сумму больше нуля'}
            </Note>
          ) : null}
          {mutation.isError ? <Note tone="error">{mutation.error.message}</Note> : null}

          <div className="uk-spacer" />
          <Button
            variant="primary"
            disabled={!amountIsValid}
            loading={mutation.isPending}
            onClick={handleConfirm}
          >
            Перевести {Number.isFinite(amountNum) ? amountNum.toFixed(2) : '0.00'} {UNIT_SYMBOL}
          </Button>
        </div>
      </Screen>
    );
  }

  return (
    <Screen>
      <ScreenHeader title="Перевести юниты" onBack={handleClose} />
      <div className="uk-stack">
        {!canTransfer ? (
          <Note tone="error">Перевод недоступен при долге. Переводить можно только с положительного баланса.</Note>
        ) : (
          <div
            style={{
              padding: 18,
              borderRadius: 22,
              background: 'var(--uk-glass)',
              border: '1px solid var(--uk-hairline)',
            }}
          >
            <div style={{ font: "600 11px 'Manrope'", letterSpacing: '.08em', textTransform: 'uppercase', color: 'var(--uk-ink-55)' }}>
              Доступно к переводу
            </div>
            <div style={{ font: "800 32px/1 'Manrope'", marginTop: 6, color: 'var(--uk-positive)' }}>
              {formatBalance(myBalance)} <span style={{ font: "600 15px 'Manrope'", color: 'var(--uk-ink-55)' }}>{UNIT_SYMBOL}</span>
            </div>
          </div>
        )}

        <div className="uk-eyebrow">Кому перевести</div>
        <div className="uk-stack" style={{ gap: 10 }}>
          {(candidates?.candidates ?? []).map((candidate) => (
            <button
              key={candidate.user.id}
              type="button"
              disabled={!canTransfer}
              onClick={() => {
                setRecipientId(candidate.user.id);
                setStep('amount');
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 13,
                padding: '14px 16px',
                borderRadius: 18,
                background: 'var(--uk-glass)',
                border: '1px solid var(--uk-hairline)',
                cursor: canTransfer ? 'pointer' : 'not-allowed',
                opacity: canTransfer ? 1 : 0.5,
                textAlign: 'left',
              }}
            >
              <div
                className="uk-avatar"
                style={{ background: avatarColor(candidate.user.id) }}
              >
                {candidateName(candidate.user).slice(0, 1).toUpperCase()}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ font: "600 15px 'Manrope'" }}>{candidateName(candidate.user)}</div>
                <div style={{ font: "400 12px 'Manrope'", color: 'var(--uk-ink-55)' }}>
                  баланс {formatBalance(candidate.current_balance)} {UNIT_SYMBOL}
                </div>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--uk-ink-45)" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 6l6 6-6 6" />
              </svg>
            </button>
          ))}
          {candidates?.candidates.length === 0 ? (
            <Note tone="info">В группе больше никого нет.</Note>
          ) : null}
        </div>

        <Note tone="info">
          Перевести можно не больше, чем есть на балансе. Показаны только активные участники, кроме вас.
        </Note>
      </div>
    </Screen>
  );
}
