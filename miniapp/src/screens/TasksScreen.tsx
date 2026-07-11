import { useState, type FormEvent } from 'react';
import { Navigate } from 'react-router-dom';

import { useCreateTask, useMarkTaskDone } from '@/api/mutations';
import { useCurrentGroup, useTasks } from '@/api/queries';
import { useAuth } from '@/auth/useAuth';
import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';
import { routes } from '@/routes/paths';
import { formatUnits } from '@/ui/format';
import { BottomSheet, Button, Card, Field, Note, Screen, Stepper, TextInput } from '@/ui/kit';
import { CheckIcon, PlusIcon } from '@/ui/icons';
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
  pending,
  disabled,
}: {
  task: TaskResponse;
  onDone: () => void;
  pending: boolean;
  disabled: boolean;
}) {
  const complete = task.remaining_in_sprint <= 0;
  return (
    <div className="uk-row">
      <button
        type="button"
        onClick={onDone}
        disabled={complete || disabled}
        aria-label={complete ? 'Задача выполнена' : `Отметить «${task.title}»`}
        style={{
          width: 30,
          height: 30,
          flex: 'none',
          borderRadius: 10,
          display: 'grid',
          placeItems: 'center',
          cursor: complete || disabled ? 'default' : 'pointer',
          background: complete ? 'var(--uk-accent-grad)' : 'transparent',
          border: complete ? 'none' : '2px solid rgba(94,199,255,.5)',
          color: 'var(--uk-on-accent)',
        }}
      >
        {pending ? (
          <span className="uk-btn-spinner" style={{ color: 'var(--uk-blue)' }} aria-hidden />
        ) : complete ? (
          <CheckIcon size={16} strokeWidth={3} />
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
        <div style={{ font: "400 12px 'Manrope'", color: 'var(--uk-ink-55)' }}>
          {task.completed_in_sprint} из {task.frequency_per_sprint} за спринт
        </div>
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

      {markDone.isError ? <Note tone="error">{markDone.error.message}</Note> : null}

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
                onDone={() => markDone.mutate(task.id)}
                pending={markDone.isPending && markDone.variables === task.id}
                disabled={markDone.isPending}
              />
            ))}
          </Card>
        </>
      )}

      {adding ? <AddTaskSheet onClose={() => setAdding(false)} /> : null}
    </Screen>
  );
}
