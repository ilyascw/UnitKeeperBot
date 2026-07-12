import { useState, type FormEvent } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';

import { useApproveTaskLog, useRejectTaskLog } from '@/api/mutations';
import { useCurrentGroup, useGroupTaskLogs, usePendingApprovals } from '@/api/queries';
import type { TaskLogStatus, TaskLogViewResponse, UserResponse } from '@/api/types';
import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';
import { routes } from '@/routes/paths';
import { formatDay, formatUnits } from '@/ui/format';
import { BottomSheet, Button, Card, Field, Note, Screen, ScreenHeader, TextInput } from '@/ui/kit';
import { CheckIcon, ClockIcon } from '@/ui/icons';

function displayName(user: UserResponse): string {
  return user.first_name ?? user.username ?? `Участник ${user.id}`;
}

function statusLabel(status: TaskLogStatus): string {
  if (status === 'completed') return 'Подтверждено';
  if (status === 'rejected') return 'Отклонено';
  return 'На подтверждении';
}

function statusColor(status: TaskLogStatus): string {
  if (status === 'completed') return 'var(--uk-positive)';
  if (status === 'rejected') return 'var(--uk-danger)';
  return 'var(--uk-warn)';
}

function LogRow({ log, actions, onReject }: { log: TaskLogViewResponse; actions: boolean; onReject: () => void }) {
  const approve = useApproveTaskLog();
  const busy = approve.isPending;
  return (
    <div className="uk-row" style={{ alignItems: 'flex-start' }}>
      <ClockIcon size={19} style={{ color: statusColor(log.status), marginTop: 2, flex: 'none' }} />
      <div className="uk-row__grow" style={{ minWidth: 0 }}>
        <div style={{ font: "700 15px 'Manrope'" }}>{log.task.title}</div>
        <div style={{ font: "400 12px 'Manrope'", color: 'var(--uk-ink-55)', marginTop: 3 }}>
          {displayName(log.performer)} · {formatDay(log.created_at)} · {formatUnits(log.task.unit_cost)} ю
        </div>
        <div style={{ font: "600 12px 'Manrope'", color: statusColor(log.status), marginTop: 5 }}>
          {statusLabel(log.status)}
        </div>
        {log.rejection_reason ? (
          <div style={{ font: "400 12px 'Manrope'", color: 'var(--uk-ink-55)', marginTop: 3 }}>
            Причина: {log.rejection_reason}
          </div>
        ) : null}
        {actions ? (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 10 }}>
            <Button variant="soft" loading={busy} onClick={() => approve.mutate(log.id)}>
              <CheckIcon size={16} /> Подтвердить
            </Button>
            <Button variant="danger" disabled={busy} onClick={onReject}>
              Отклонить
            </Button>
          </div>
        ) : null}
        {approve.isError ? <Note tone="error">{approve.error.message}</Note> : null}
      </div>
    </div>
  );
}

function RejectSheet({ log, onClose }: { log: TaskLogViewResponse; onClose: () => void }) {
  const reject = useRejectTaskLog();
  const [reason, setReason] = useState('');
  const submit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    if (!reason.trim()) return;
    reject.mutate({ logId: log.id, reason: reason.trim() }, { onSuccess: onClose });
  };
  return (
    <BottomSheet onClose={() => (reject.isPending ? undefined : onClose())}>
      <div style={{ font: "800 20px 'Manrope'", textAlign: 'center', marginBottom: 16 }}>Отклонить отметку</div>
      <form className="uk-stack" onSubmit={submit}>
        <Field label="Причина" hint="Её увидит исполнитель.">
          <TextInput value={reason} onChange={(e) => setReason(e.currentTarget.value)} autoFocus disabled={reject.isPending} maxLength={500} />
        </Field>
        {reject.isError ? <Note tone="error">{reject.error.message}</Note> : null}
        <Button variant="danger" type="submit" loading={reject.isPending} disabled={!reason.trim()}>
          Отклонить
        </Button>
      </form>
    </BottomSheet>
  );
}

/** Approval queue and task-log history for every active group member. */
export function TaskLogsScreen() {
  const navigate = useNavigate();
  const group = useCurrentGroup();
  const pending = usePendingApprovals(true);
  const groupLogs = useGroupTaskLogs(true);
  const [rejecting, setRejecting] = useState<TaskLogViewResponse | null>(null);

  if (group.isPending || pending.isPending || groupLogs.isPending) {
    return <Loader title="Загружаем отметки…" />;
  }
  if (group.data === null) return <Navigate to={routes.onboarding} replace />;
  if (groupLogs.isError || pending.isError) {
    const error = groupLogs.error ?? pending.error;
    return (
      <ErrorState
        title="Не удалось загрузить"
        description={error?.message ?? ''}
        onRetry={() => void Promise.all([pending.refetch(), groupLogs.refetch()])}
      />
    );
  }
  const pendingItems = pending.data?.items ?? [];
  const historyItems = groupLogs.data?.items ?? [];
  return (
    <Screen>
      <ScreenHeader title="Отметки" onBack={() => navigate(routes.tasks)} />
      <section className="uk-stack" style={{ marginBottom: 20 }}>
        <div className="uk-eyebrow">На подтверждении</div>
        {pendingItems.length ? (
          <Card flush>
            {pendingItems.map((log) => <LogRow key={log.id} log={log} actions onReject={() => setRejecting(log)} />)}
          </Card>
        ) : <Note tone="info">Нет отметок, ожидающих вашего решения.</Note>}
      </section>
      <section className="uk-stack">
        <div className="uk-eyebrow">История группы</div>
        {historyItems.length ? (
          <Card flush>{historyItems.map((log) => <LogRow key={log.id} log={log} actions={false} onReject={() => undefined} />)}</Card>
        ) : <Note tone="info">История появится после первой отметки выполнения.</Note>}
      </section>
      {rejecting ? <RejectSheet log={rejecting} onClose={() => setRejecting(null)} /> : null}
    </Screen>
  );
}
