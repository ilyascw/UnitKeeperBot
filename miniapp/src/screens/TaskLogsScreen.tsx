import { useState } from 'react';
import { Navigate, useNavigate } from '@/routes/navigation';

import { useCurrentGroup, useGroupTaskLogs, usePendingApprovals } from '@/api/queries';
import { useAuth } from '@/auth/useAuth';
import type { TaskLogViewResponse } from '@/api/types';
import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';
import { LogRow, RejectSheet } from '@/components/TaskLogRow';
import { routes } from '@/routes/paths';
import { Card, Note, Screen, ScreenHeader } from '@/ui/kit';

/** Approval queue and task-log history for every active group member. */
export function TaskLogsScreen() {
  const navigate = useNavigate();
  const { context } = useAuth();
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
  const myUserId = context?.user?.id;
  // Logs someone else is waiting on your decision for already live in the
  // queue above — only hide those from history to avoid duplicating them.
  // A log still pending on your own mark (nobody else has decided it yet)
  // has no other home, so it stays visible here.
  const historyItems = (groupLogs.data?.items ?? []).filter(
    (log) => log.status !== 'pending' || log.performer.id === myUserId,
  );
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
