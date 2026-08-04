import { useState, type FormEvent } from 'react';

import { useApproveTaskLog, useRejectTaskLog } from '@/api/mutations';
import type { TaskLogStatus, TaskLogViewResponse, UserResponse } from '@/api/types';
import { UNIT_SYMBOL, formatDay, formatUnits } from '@/ui/format';
import { BottomSheet, Button, Field, Note, TextInput } from '@/components/ui/app-kit';
import { CheckIcon } from '@/ui/icons';

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

/** A task-log row with inline approve/reject actions — used wherever a pending queue is shown. */
export function LogRow({
  log,
  actions,
  onReject,
}: {
  log: TaskLogViewResponse;
  actions: boolean;
  onReject: () => void;
}) {
  const approve = useApproveTaskLog();
  const busy = approve.isPending;
  return (
    <div className="uk-row" style={{ alignItems: 'flex-start' }}>
      <div className="uk-row__grow" style={{ minWidth: 0 }}>
        <div style={{ font: "700 15px 'Manrope'" }}>{log.task.title}</div>
        <div style={{ font: "400 12px 'Manrope'", color: 'var(--uk-ink-55)', marginTop: 3 }}>
          {displayName(log.performer)} · {formatDay(log.created_at)} ·{' '}
          {formatUnits(log.task.unit_cost)} {UNIT_SYMBOL}
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

export function RejectSheet({ log, onClose }: { log: TaskLogViewResponse; onClose: () => void }) {
  const reject = useRejectTaskLog();
  const [reason, setReason] = useState('');
  const submit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    if (!reason.trim()) return;
    reject.mutate({ logId: log.id, reason: reason.trim() }, { onSuccess: onClose });
  };
  return (
    <BottomSheet onClose={() => (reject.isPending ? undefined : onClose())}>
      <div style={{ font: "800 20px 'Manrope'", textAlign: 'center', marginBottom: 16 }}>
        Отклонить отметку
      </div>
      <form className="uk-stack" onSubmit={submit}>
        <Field label="Причина" hint="Её увидит исполнитель.">
          <TextInput
            value={reason}
            onChange={(e) => setReason(e.currentTarget.value)}
            autoFocus
            disabled={reject.isPending}
            maxLength={500}
          />
        </Field>
        {reject.isError ? <Note tone="error">{reject.error.message}</Note> : null}
        <Button variant="danger" type="submit" loading={reject.isPending} disabled={!reason.trim()}>
          Отклонить
        </Button>
      </form>
    </BottomSheet>
  );
}
