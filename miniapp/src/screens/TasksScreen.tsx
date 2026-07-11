import { useEffect, useState, type FormEvent } from 'react';
import { Navigate } from 'react-router-dom';

import { useCreateTask, useMarkTaskDone } from '@/api/mutations';
import { useCurrentGroup, useTasks } from '@/api/queries';
import { useAuth } from '@/auth/useAuth';
import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';
import { routes } from '@/routes/paths';
import { formatUnits } from '@/ui/format';
import { BottomSheet, Button, Card, Field, Note, Screen, Stepper, TextInput, Toast } from '@/ui/kit';
import { CheckIcon, ClockIcon, PlusIcon } from '@/ui/icons';
import type { TaskResponse } from '@/api/types';

/** Owner-only sheet for adding a recurring task. */
function AddTaskSheet({ onClose }: { onClose: () => void }) {
  const create = useCreateTask();
  const [title, setTitle] = useState('');
  const [frequency, setFrequency] = useState(1);
  const [cost, setCost] = useState('');

  const costValue = Number.parseFloat(cost.replace(',', '.'));
  const costValid = Number.isFinite(costValue) && costValue >= 0;
  const canSubmit = title.trim().length > 0 && costValid;

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    if (!canSubmit) return;
    create.mutate(
      { title: title.trim(), frequency_per_sprint: frequency, unit_cost: String(costValue) },
      { onSuccess: onClose },
    );
  };

  return (
    <BottomSheet onClose={() => (create.isPending ? undefined : onClose())}>
      <div style={{ textAlign: 'center', font: "800 20px 'Manrope'", marginBottom: 18 }}>
        Новая задача
      </div>
      <form onSubmit={handleSubmit} className="uk-stack">
        <Field label="Название">
          <TextInput
            value={title}
            onChange={(e) => setTitle(e.currentTarget.value)}
            placeholder="Например, помыть посуду"
            maxLength={255}
            autoFocus
          />
        </Field>
        <Stepper
          label="Сколько раз за спринт"
          value={frequency}
          min={1}
          max={99}
          suffix="раз"
          onChange={setFrequency}
          disabled={create.isPending}
        />
        <Field label="Стоимость, юниты" hint="Сколько юнитов начисляется за одно выполнение.">
          <TextInput
            value={cost}
            onChange={(e) => setCost(e.currentTarget.value)}
            inputMode="decimal"
            placeholder="5"
          />
        </Field>
        {create.isError ? <Note tone="error">{create.error.message}</Note> : null}
        <Button type="submit" variant="primary" loading={create.isPending} disabled={!canSubmit}>
          Добавить задачу
        </Button>
      </form>
    </BottomSheet>
  );
}

function TaskRow({
  task,
  onDone,
  loading,
  busy,
}: {
  task: TaskResponse;
  onDone: () => void;
  /** This task's own completion request is in flight. */
  loading: boolean;
  /** Some completion request is in flight (blocks all rows). */
  busy: boolean;
}) {
  // Backend-derived states (source of truth, survives reload):
  //  complete  — every slot confirmed (remaining 0)
  //  heldFull  — remaining slots all occupied by pending holds (available 0)
  //  markable  — at least one free slot (available > 0)
  const complete = task.remaining_in_sprint <= 0;
  const markable = task.available_in_sprint > 0;
  const heldFull = !complete && !markable;
  const locked = !markable || busy;

  return (
    <div className="uk-row">
      <button
        type="button"
        onClick={onDone}
        disabled={locked}
        aria-label={
          complete
            ? 'Задача выполнена'
            : heldFull
              ? 'Ждёт подтверждения'
              : `Отметить «${task.title}»`
        }
        style={{
          width: 30,
          height: 30,
          flex: 'none',
          borderRadius: 10,
          display: 'grid',
          placeItems: 'center',
          cursor: locked ? 'default' : 'pointer',
          background: complete ? 'var(--uk-accent-grad)' : 'transparent',
          border: complete
            ? 'none'
            : heldFull
              ? '2px solid rgba(255,200,97,.6)'
              : '2px solid rgba(94,199,255,.5)',
          color: complete ? 'var(--uk-on-accent)' : 'var(--uk-warn)',
        }}
      >
        {loading ? (
          <span className="uk-btn-spinner" style={{ color: 'var(--uk-blue)' }} aria-hidden />
        ) : complete ? (
          <CheckIcon size={16} strokeWidth={3} />
        ) : heldFull ? (
          <ClockIcon size={16} />
        ) : null}
      </button>
      <div className="uk-row__grow">
        <div
          style={{
            font: "600 15px 'Manrope'",
            color: complete ? 'var(--uk-ink-55)' : 'var(--uk-ink)',
          }}
        >
          {task.title}
        </div>
        {heldFull ? (
          <div
            style={{
              font: "600 12px 'Manrope'",
              color: 'var(--uk-warn)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 5,
            }}
          >
            <ClockIcon size={13} /> Ждёт подтверждения
          </div>
        ) : (
          <div style={{ font: "400 12px 'Manrope'", color: 'var(--uk-ink-55)' }}>
            {task.completed_in_sprint} из {task.frequency_per_sprint} за спринт
            {task.pending_in_sprint > 0 ? (
              <span style={{ color: 'var(--uk-warn)' }}>
                {' · '}
                {task.pending_in_sprint} на подтверждении
              </span>
            ) : null}
          </div>
        )}
      </div>
      <span
        style={{
          font: "700 15px 'Manrope'",
          color: complete ? 'var(--uk-ink-45)' : 'var(--uk-teal)',
        }}
      >
        {formatUnits(task.unit_cost)} ю
      </span>
    </div>
  );
}

/**
 * Tasks section. Lists the group's recurring tasks with their per-sprint
 * progress; any member can log a completion, and the owner can add tasks.
 */
export function TasksScreen() {
  const { context } = useAuth();
  const group = useCurrentGroup();
  const { data: tasks, isPending, isError, error, refetch } = useTasks();
  const markDone = useMarkTaskDone();
  const [adding, setAdding] = useState(false);
  const [toast, setToast] = useState<{ tone: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 2800);
    return () => clearTimeout(timer);
  }, [toast]);

  const handleDone = (task: TaskResponse): void => {
    // The pending / completed state itself comes from the refetched task list
    // (invalidated by the mutation); the toast just confirms the action landed.
    markDone.mutate(task.id, {
      onSuccess: (log) =>
        setToast({
          tone: 'success',
          text: log.status === 'pending' ? 'Отправлено на подтверждение' : 'Задача засчитана',
        }),
      onError: () => setToast({ tone: 'error', text: 'Не удалось отметить задачу' }),
    });
  };

  if (group.data === null) return <Navigate to={routes.onboarding} replace />;
  if (isPending) return <Loader title="Загружаем задачи…" />;
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

  const isOwner = context?.user?.id === group.data?.owner_user_id;

  return (
    <Screen>
      <div className="uk-header" style={{ justifyContent: 'space-between' }}>
        <div className="uk-header__title">Задачи</div>
        {isOwner ? (
          <button
            type="button"
            className="uk-back"
            aria-label="Добавить задачу"
            onClick={() => setAdding(true)}
          >
            <PlusIcon size={24} />
          </button>
        ) : null}
      </div>

      {tasks.length === 0 ? (
        <Card style={{ padding: 22, borderRadius: 20, textAlign: 'center' }}>
          <div style={{ font: "700 16px 'Manrope'" }}>Пока нет задач</div>
          <div style={{ font: "400 13px 'Manrope'", color: 'var(--uk-ink-55)', marginTop: 6 }}>
            {isOwner
              ? 'Добавьте первую задачу — участники смогут отмечать её выполнение.'
              : 'Владелец группы ещё не добавил задачи.'}
          </div>
          {isOwner ? (
            <div style={{ marginTop: 16 }}>
              <Button variant="primary" onClick={() => setAdding(true)}>
                <PlusIcon size={18} /> Добавить задачу
              </Button>
            </div>
          ) : null}
        </Card>
      ) : (
        <>
          <Note tone="info">Отметьте выполнение — оно уйдёт владельцу на подтверждение.</Note>
          <Card flush>
            {tasks.map((task) => (
              <TaskRow
                key={task.id}
                task={task}
                onDone={() => handleDone(task)}
                loading={markDone.isPending && markDone.variables === task.id}
                busy={markDone.isPending}
              />
            ))}
          </Card>
        </>
      )}

      {toast ? <Toast tone={toast.tone} message={toast.text} /> : null}
      {adding ? <AddTaskSheet onClose={() => setAdding(false)} /> : null}
    </Screen>
  );
}
