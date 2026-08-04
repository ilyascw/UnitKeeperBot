import { useEffect, useState, type FormEvent } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Navigate, useNavigate } from '@/routes/navigation';

import {
  useCancelTaskLog,
  useCreateTask,
  useDecreaseTaskFrequency,
  useDeleteTask,
  useIncreaseTaskFrequency,
  useImportTasks,
  useMarkTaskDone,
  useUpdateTask,
} from '@/api/mutations';
import { useCurrentGroup, useMyTaskLogs, useTasks } from '@/api/queries';
import { refreshTaskData } from '@/api/query-refresh';
import { ApiError } from '@/api/client';
import { useAuth } from '@/auth/useAuth';
import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';
import { routes } from '@/routes/paths';
import { UNIT_SYMBOL, formatUnits } from '@/ui/format';
import {
  BottomSheet,
  Button,
  Card,
  Field,
  Note,
  Screen,
  Stepper,
  TextInput,
  Toast,
} from '@/ui/kit';
import { CheckIcon, ClockIcon, PencilIcon, PlusIcon, RefreshIcon, TrashIcon } from '@/ui/icons';
import type { BulkImportTaskItem, TaskImportRowError, TaskResponse } from '@/api/types';

function parseCost(value: string): number {
  return Number.parseFloat(value.replace(',', '.'));
}

function taskIsMarkable(task: TaskResponse): boolean {
  return task.available_in_sprint > 0;
}

function taskIsPaused(task: TaskResponse): boolean {
  return task.frequency_per_sprint === 0;
}

function taskIsComplete(task: TaskResponse): boolean {
  return !taskIsPaused(task) && task.remaining_in_sprint <= 0;
}

function taskIsHeldFull(task: TaskResponse): boolean {
  return !taskIsPaused(task) && !taskIsComplete(task) && !taskIsMarkable(task);
}

function parseImportRows(value: string): {
  items: BulkImportTaskItem[];
  errors: TaskImportRowError[];
} {
  const errors: TaskImportRowError[] = [];
  const items: BulkImportTaskItem[] = [];
  value.split(/\r?\n/).forEach((raw, index) => {
    if (!raw.trim()) return;
    const cells = raw.split(raw.includes('\t') ? '\t' : ';').map((cell) => cell.trim());
    if (cells.length !== 3) {
      errors.push({
        index,
        field: 'row',
        message: 'Нужны три колонки: название, частота, стоимость',
      });
      return;
    }
    const [title, frequency, cost] = cells;
    const parsedFrequency = Number(frequency);
    const parsedCost = Number(cost.replace(',', '.'));
    if (!title) errors.push({ index, field: 'title', message: 'Укажите название' });
    if (!Number.isInteger(parsedFrequency) || parsedFrequency < 0) {
      errors.push({
        index,
        field: 'frequency_per_sprint',
        message: 'Частота должна быть целым неотрицательным числом',
      });
    }
    if (!Number.isFinite(parsedCost) || parsedCost < 0) {
      errors.push({
        index,
        field: 'unit_cost',
        message: 'Стоимость должна быть числом не меньше нуля',
      });
    }
    items.push({ title, frequency_per_sprint: parsedFrequency, unit_cost: String(parsedCost) });
  });
  if (!items.length && !errors.length)
    errors.push({ index: 0, field: 'row', message: 'Добавьте хотя бы одну строку' });
  return { items, errors };
}

function backendImportErrors(error: Error): TaskImportRowError[] {
  if (!(error instanceof ApiError) || !error.details || typeof error.details !== 'object')
    return [];
  const candidates = (error.details as { errors?: unknown }).errors;
  if (!Array.isArray(candidates)) return [];
  return candidates.flatMap((item) => {
    if (!item || typeof item !== 'object') return [];
    const row = item as Partial<TaskImportRowError>;
    return typeof row.index === 'number' &&
      typeof row.field === 'string' &&
      typeof row.message === 'string'
      ? [{ index: row.index, field: row.field, message: row.message }]
      : [];
  });
}

function ImportTasksSheet({
  onClose,
  onImported,
}: {
  onClose: () => void;
  onImported: (count: number) => void;
}) {
  const importTasks = useImportTasks();
  const [source, setSource] = useState('');
  const [localErrors, setLocalErrors] = useState<TaskImportRowError[]>([]);
  const serverErrors = importTasks.isError ? backendImportErrors(importTasks.error) : [];
  const errors = localErrors.length ? localErrors : serverErrors;
  const submit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    const result = parseImportRows(source);
    setLocalErrors(result.errors);
    if (result.errors.length) return;
    importTasks.mutate(result.items, {
      onSuccess: (tasks) => {
        onImported(tasks.length);
        onClose();
      },
    });
  };
  return (
    <BottomSheet onClose={() => (importTasks.isPending ? undefined : onClose())}>
      <div style={{ font: "800 20px 'Manrope'", textAlign: 'center', marginBottom: 12 }}>
        Импорт задач
      </div>
      <form className="uk-stack" onSubmit={submit}>
        <Field
          label="Таблица задач"
          hint="Вставьте строки из таблицы: название, частота, стоимость. Колонки разделяйте табуляцией или точкой с запятой."
        >
          <textarea
            className="uk-input"
            value={source}
            onChange={(e) => {
              setSource(e.currentTarget.value);
              setLocalErrors([]);
            }}
            disabled={importTasks.isPending}
            rows={7}
            placeholder={'Мыть посуду\t3\t5\nПылесосить\t1\t10'}
            style={{ resize: 'vertical', paddingTop: 11 }}
          />
        </Field>
        {errors.length ? (
          <Note tone="error">
            {errors.map((error) => (
              <div key={`${error.index}-${error.field}`}>
                Строка {error.index + 1}: {error.message}
              </div>
            ))}
          </Note>
        ) : null}
        {importTasks.isError && !errors.length ? (
          <Note tone="error">{importTasks.error.message}</Note>
        ) : null}
        <Button type="submit" variant="primary" loading={importTasks.isPending}>
          Импортировать
        </Button>
      </form>
    </BottomSheet>
  );
}

/** Owner-only sheet for adding or editing a recurring task. */
function TaskFormSheet({
  task,
  onClose,
  onSaved,
}: {
  task?: TaskResponse;
  onClose: () => void;
  onSaved: (message: string) => void;
}) {
  const create = useCreateTask();
  const update = useUpdateTask();
  const isEditing = task !== undefined;
  const pending = create.isPending || update.isPending;
  const [title, setTitle] = useState(task?.title ?? '');
  const [frequency, setFrequency] = useState(task?.frequency_per_sprint ?? 1);
  const [cost, setCost] = useState(task?.unit_cost ?? '');

  const costValue = parseCost(cost);
  const costValid = Number.isFinite(costValue) && costValue >= 0;
  const canSubmit = title.trim().length > 0 && costValid;

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    if (!canSubmit) return;
    if (isEditing) {
      update.mutate(
        {
          taskId: task.id,
          body: {
            title: title.trim(),
            frequency_per_sprint: frequency,
            unit_cost: String(costValue),
          },
        },
        {
          onSuccess: () => {
            onSaved('Задача обновлена');
            onClose();
          },
        },
      );
      return;
    }
    create.mutate(
      { title: title.trim(), frequency_per_sprint: frequency, unit_cost: String(costValue) },
      {
        onSuccess: () => {
          onSaved('Задача добавлена');
          onClose();
        },
      },
    );
  };

  return (
    <BottomSheet onClose={() => (pending ? undefined : onClose())}>
      <div style={{ textAlign: 'center', font: "800 20px 'Manrope'", marginBottom: 18 }}>
        {isEditing ? 'Редактировать задачу' : 'Новая задача'}
      </div>
      <form onSubmit={handleSubmit} className="uk-stack">
        <Field label="Название">
          <TextInput
            name="title"
            value={title}
            onChange={(e) => setTitle(e.currentTarget.value)}
            placeholder="Например, помыть посуду"
            maxLength={255}
            disabled={pending}
            autoFocus
            enterKeyHint="next"
          />
        </Field>
        <Stepper
          label="Сколько раз за спринт"
          value={frequency}
          min={0}
          max={99}
          suffix="раз"
          onChange={setFrequency}
          disabled={pending}
        />
        <Field label="Стоимость, юниты" hint="Сколько юнитов начисляется за одно выполнение.">
          <TextInput
            name="unit_cost"
            value={cost}
            onChange={(e) => setCost(e.currentTarget.value)}
            inputMode="decimal"
            placeholder="5"
            disabled={pending}
            enterKeyHint="done"
          />
        </Field>
        {create.isError ? <Note tone="error">{create.error.message}</Note> : null}
        {update.isError ? <Note tone="error">{update.error.message}</Note> : null}
        <Button type="submit" variant="primary" loading={pending} disabled={!canSubmit}>
          {isEditing ? 'Сохранить изменения' : 'Добавить задачу'}
        </Button>
      </form>
    </BottomSheet>
  );
}

function DeleteTaskSheet({
  task,
  onClose,
  onDeleted,
}: {
  task: TaskResponse;
  onClose: () => void;
  onDeleted: () => void;
}) {
  const deleteTask = useDeleteTask();

  const handleDelete = (): void => {
    deleteTask.mutate(task.id, { onSuccess: onDeleted });
  };

  return (
    <BottomSheet onClose={() => (deleteTask.isPending ? undefined : onClose())}>
      <div style={{ textAlign: 'center', font: "800 20px 'Manrope'", marginBottom: 10 }}>
        Удалить задачу?
      </div>
      <Note tone="warn">
        «{task.title}» исчезнет из активного списка. Уже созданные отметки выполнения сохранятся в
        истории.
      </Note>
      {deleteTask.isError ? <Note tone="error">{deleteTask.error.message}</Note> : null}
      <div className="uk-stack" style={{ marginTop: 16 }}>
        <Button variant="danger" loading={deleteTask.isPending} onClick={handleDelete}>
          <TrashIcon size={18} /> Удалить
        </Button>
        <Button variant="ghost" disabled={deleteTask.isPending} onClick={onClose}>
          Оставить задачу
        </Button>
      </div>
    </BottomSheet>
  );
}

function TaskDetailSheet({
  task,
  isOwner,
  markLoading,
  markBusy,
  onClose,
  onDone,
  onCancel,
  myPendingLogId,
  cancelLoading,
  onEdit,
  onDelete,
}: {
  task: TaskResponse;
  isOwner: boolean;
  markLoading: boolean;
  markBusy: boolean;
  onClose: () => void;
  onDone: () => void;
  /** Undo the caller's own not-yet-reviewed mark on this task. */
  onCancel: () => void;
  /** The id of the current user's own pending log for this task, if any. */
  myPendingLogId: number | null;
  cancelLoading: boolean;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const increase = useIncreaseTaskFrequency();
  const decrease = useDecreaseTaskFrequency();
  const paused = taskIsPaused(task);
  const complete = taskIsComplete(task);
  const heldFull = taskIsHeldFull(task);
  const markable = taskIsMarkable(task);
  const canCancel = heldFull && myPendingLogId !== null;
  const adjusting = increase.isPending || decrease.isPending;

  return (
    <BottomSheet onClose={onClose}>
      <div className="uk-stack">
        <div>
          <div style={{ font: "800 22px/1.2 'Manrope'" }}>{task.title}</div>
          <div style={{ font: "500 13px 'Manrope'", color: 'var(--uk-ink-55)', marginTop: 6 }}>
            {formatUnits(task.unit_cost)} {UNIT_SYMBOL} за выполнение
          </div>
        </div>

        <Card style={{ padding: 14, borderRadius: 18 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <div className="uk-eyebrow">Прогресс</div>
              <div style={{ font: "800 22px 'Manrope'", marginTop: 4 }}>
                {task.completed_in_sprint}/{task.frequency_per_sprint}
              </div>
            </div>
            <div>
              <div className="uk-eyebrow">Доступно</div>
              <div style={{ font: "800 22px 'Manrope'", marginTop: 4 }}>
                {task.available_in_sprint}
              </div>
            </div>
          </div>
          {task.pending_in_sprint > 0 ? (
            <div style={{ marginTop: 12, font: "600 12.5px 'Manrope'", color: 'var(--uk-warn)' }}>
              {task.pending_in_sprint} на подтверждении
            </div>
          ) : null}
        </Card>

        {paused ? (
          <Note tone="info">Задача не запланирована на текущий спринт.</Note>
        ) : heldFull ? (
          <Note tone="warn">Все свободные слоты сейчас заняты отметками на подтверждении.</Note>
        ) : complete ? (
          <Note tone="info">Лимит на этот спринт уже выполнен.</Note>
        ) : null}

        <Button
          variant="primary"
          loading={markLoading}
          disabled={!markable || markBusy}
          onClick={onDone}
        >
          <CheckIcon size={18} /> Отметить выполнение
        </Button>
        {canCancel ? (
          <Button variant="soft" loading={cancelLoading} disabled={markBusy} onClick={onCancel}>
            Отменить отметку
          </Button>
        ) : null}

        {isOwner ? (
          <>
            <div className="uk-divider" />
            <div>
              <div className="uk-eyebrow" style={{ marginBottom: 8 }}>
                Частота за спринт
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <Button
                  variant="soft"
                  disabled={adjusting || task.frequency_per_sprint <= 0}
                  loading={decrease.isPending}
                  onClick={() => decrease.mutate(task.id)}
                >
                  −1
                </Button>
                <Button
                  variant="soft"
                  disabled={adjusting}
                  loading={increase.isPending}
                  onClick={() => increase.mutate(task.id)}
                >
                  +1
                </Button>
              </div>
              {decrease.isError ? <Note tone="error">{decrease.error.message}</Note> : null}
              {increase.isError ? <Note tone="error">{increase.error.message}</Note> : null}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <Button variant="ghost" onClick={onEdit}>
                <PencilIcon size={17} /> Изменить
              </Button>
              <Button variant="danger" onClick={onDelete}>
                <TrashIcon size={17} /> Удалить
              </Button>
            </div>
          </>
        ) : null}
      </div>
    </BottomSheet>
  );
}

function TaskRow({
  task,
  onDone,
  onOpen,
  onCancel,
  myPendingLogId,
  loading,
  busy,
}: {
  task: TaskResponse;
  onDone: () => void;
  onOpen: () => void;
  /** Undo the caller's own not-yet-reviewed mark on this task. */
  onCancel: () => void;
  /** The id of the current user's own pending log for this task, if any. */
  myPendingLogId: number | null;
  /** This task's own completion/cancel request is in flight. */
  loading: boolean;
  /** Some completion/cancel request is in flight (blocks all rows). */
  busy: boolean;
}) {
  // Backend-derived states (source of truth, survives reload):
  //  complete  — every slot confirmed (remaining 0)
  //  heldFull  — remaining slots all occupied by pending holds (available 0)
  //  markable  — at least one free slot (available > 0)
  const paused = taskIsPaused(task);
  const complete = taskIsComplete(task);
  const markable = taskIsMarkable(task);
  const heldFull = taskIsHeldFull(task);
  const canCancel = heldFull && myPendingLogId !== null;
  const locked = (!markable && !canCancel) || busy;

  return (
    <div className="uk-row">
      <button
        type="button"
        onClick={canCancel ? onCancel : onDone}
        disabled={locked}
        aria-label={
          paused
            ? 'Задача не запланирована на текущий спринт'
            : complete
              ? 'Задача выполнена'
              : canCancel
                ? 'Отменить отметку'
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
          background: complete ? 'var(--uk-accent)' : 'transparent',
          border: complete
            ? 'none'
            : heldFull
              ? '2px solid rgba(217,173,102,.6)'
              : '2px solid rgba(124,166,217,.5)',
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
      <button
        type="button"
        className="uk-row__grow"
        onClick={onOpen}
        style={{
          minWidth: 0,
          padding: 0,
          border: 'none',
          background: 'none',
          color: 'inherit',
          textAlign: 'left',
          cursor: 'pointer',
        }}
        aria-label={`Открыть задачу «${task.title}»`}
      >
        <div
          style={{
            font: "600 15px 'Manrope'",
            color: complete ? 'var(--uk-ink-55)' : 'var(--uk-ink)',
          }}
        >
          {task.title}
        </div>
        {paused ? (
          <div style={{ font: "600 12px 'Manrope'", color: 'var(--uk-ink-55)' }}>
            Не запланировано на этот спринт
          </div>
        ) : heldFull ? (
          <div style={{ font: "600 12px 'Manrope'", color: 'var(--uk-warn)' }}>
            Ждёт подтверждения{canCancel ? ' · нажмите, чтобы отменить' : ''}
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
      </button>
      <span
        style={{
          font: "700 15px 'Manrope'",
          color: complete ? 'var(--uk-ink-45)' : 'var(--uk-teal)',
        }}
      >
        {formatUnits(task.unit_cost)} {UNIT_SYMBOL}
      </span>
    </div>
  );
}

/**
 * Tasks section. Lists the group's recurring tasks with their per-sprint
 * progress; any member can log a completion, and the owner can add tasks.
 */
export function TasksScreen() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { context } = useAuth();
  const group = useCurrentGroup();
  const { data: tasks, isPending, isError, error, refetch } = useTasks();
  const myTaskLogs = useMyTaskLogs();
  const markDone = useMarkTaskDone();
  const cancelLog = useCancelTaskLog();
  const [adding, setAdding] = useState(false);
  const [importing, setImporting] = useState(false);
  const [addMenuOpen, setAddMenuOpen] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null);
  const [editingTaskId, setEditingTaskId] = useState<number | null>(null);
  const [deletingTaskId, setDeletingTaskId] = useState<number | null>(null);
  const [toast, setToast] = useState<{ tone: 'success' | 'error'; text: string } | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 2800);
    return () => clearTimeout(timer);
  }, [toast]);

  useEffect(() => {
    if (!tasks) return;
    if (selectedTaskId !== null && !tasks.some((task) => task.id === selectedTaskId)) {
      setSelectedTaskId(null);
    }
    if (editingTaskId !== null && !tasks.some((task) => task.id === editingTaskId)) {
      setEditingTaskId(null);
    }
    if (deletingTaskId !== null && !tasks.some((task) => task.id === deletingTaskId)) {
      setDeletingTaskId(null);
    }
  }, [deletingTaskId, editingTaskId, selectedTaskId, tasks]);

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

  const handleCancel = (logId: number): void => {
    cancelLog.mutate(logId, {
      onSuccess: () => setToast({ tone: 'success', text: 'Отметка отменена' }),
      onError: () => setToast({ tone: 'error', text: 'Не удалось отменить отметку' }),
    });
  };

  if (group.data === null) return <Navigate to={routes.onboarding} replace />;
  if (isPending) return <Loader title="Загружаем задачи…" />;
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

  const isOwner = context?.user?.id === group.data?.owner_user_id;
  const todoTasks = tasks
    .filter((task) => task.frequency_per_sprint > 0)
    .sort((a, b) => b.frequency_per_sprint - a.frequency_per_sprint);
  const backlogTasks = tasks
    .filter((task) => task.frequency_per_sprint === 0)
    .sort((a, b) => b.frequency_per_sprint - a.frequency_per_sprint);
  const myPendingLogByTask = new Map<number, number>();
  for (const log of myTaskLogs.data?.items ?? []) {
    if (log.status === 'pending' && !myPendingLogByTask.has(log.task.id)) {
      myPendingLogByTask.set(log.task.id, log.id);
    }
  }
  const selectedTask =
    selectedTaskId === null ? null : (tasks.find((task) => task.id === selectedTaskId) ?? null);
  const editingTask =
    editingTaskId === null ? null : (tasks.find((task) => task.id === editingTaskId) ?? null);
  const deletingTask =
    deletingTaskId === null ? null : (tasks.find((task) => task.id === deletingTaskId) ?? null);

  const handleRefresh = async (): Promise<void> => {
    if (isRefreshing) return;

    setIsRefreshing(true);

    try {
      await refreshTaskData(queryClient, {
        refetchType: 'all',
        throwOnError: true,
      });
      setToast({ tone: 'success', text: 'Данные обновлены' });
    } catch {
      setToast({ tone: 'error', text: 'Не удалось обновить данные' });
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <Screen>
      <div className="uk-header" style={{ justifyContent: 'space-between' }}>
        <div className="uk-header__title">Задачи</div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            type="button"
            className="uk-back"
            aria-label="Открыть отметки"
            onClick={() => navigate(routes.taskLogs)}
          >
            <ClockIcon size={22} />
          </button>
          <button
            type="button"
            className="uk-back"
            aria-label="Обновить задачи"
            aria-busy={isRefreshing}
            disabled={isRefreshing}
            onClick={() => void handleRefresh()}
          >
            <RefreshIcon
              size={22}
              className={isRefreshing ? 'uk-refresh-icon--spinning' : undefined}
            />
          </button>
          {isOwner ? (
            <button
              type="button"
              className="uk-back"
              aria-label="Добавить задачу"
              onClick={() => setAddMenuOpen(true)}
            >
              <PlusIcon size={24} />
            </button>
          ) : null}
        </div>
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
            <div style={{ marginTop: 16, display: 'grid', gap: 8 }}>
              <Button variant="primary" onClick={() => setAdding(true)}>
                <PlusIcon size={18} /> Добавить задачу
              </Button>
            </div>
          ) : null}
        </Card>
      ) : (
        <>
          <Note tone="info">Отметьте выполнение — оно уйдёт владельцу на подтверждение.</Note>
          {todoTasks.length > 0 ? (
            <>
              <div className="uk-eyebrow">Нужно сделать</div>
              <Card flush>
                {todoTasks.map((task) => (
                  <TaskRow
                    key={task.id}
                    task={task}
                    onDone={() => handleDone(task)}
                    onOpen={() => setSelectedTaskId(task.id)}
                    onCancel={() => {
                      const logId = myPendingLogByTask.get(task.id);
                      if (logId !== undefined) handleCancel(logId);
                    }}
                    myPendingLogId={myPendingLogByTask.get(task.id) ?? null}
                    loading={
                      (markDone.isPending && markDone.variables === task.id) ||
                      (cancelLog.isPending &&
                        cancelLog.variables === myPendingLogByTask.get(task.id))
                    }
                    busy={markDone.isPending || cancelLog.isPending}
                  />
                ))}
              </Card>
            </>
          ) : null}
          {backlogTasks.length > 0 ? (
            <>
              <div className="uk-eyebrow">Бэклог</div>
              <Card flush>
                {backlogTasks.map((task) => (
                  <TaskRow
                    key={task.id}
                    task={task}
                    onDone={() => handleDone(task)}
                    onOpen={() => setSelectedTaskId(task.id)}
                    onCancel={() => {
                      const logId = myPendingLogByTask.get(task.id);
                      if (logId !== undefined) handleCancel(logId);
                    }}
                    myPendingLogId={myPendingLogByTask.get(task.id) ?? null}
                    loading={markDone.isPending && markDone.variables === task.id}
                    busy={markDone.isPending || cancelLog.isPending}
                  />
                ))}
              </Card>
            </>
          ) : null}
        </>
      )}

      {toast ? <Toast tone={toast.tone} message={toast.text} /> : null}
      {addMenuOpen ? (
        <BottomSheet onClose={() => setAddMenuOpen(false)}>
          <div style={{ display: 'grid', gap: 8 }}>
            <Button
              variant="primary"
              onClick={() => {
                setAddMenuOpen(false);
                setAdding(true);
              }}
            >
              <PlusIcon size={18} /> Добавить задачу
            </Button>
            <Button
              variant="soft"
              onClick={() => {
                setAddMenuOpen(false);
                setImporting(true);
              }}
            >
              Импортировать таблицу
            </Button>
          </div>
        </BottomSheet>
      ) : null}
      {adding ? (
        <TaskFormSheet
          onClose={() => setAdding(false)}
          onSaved={(text) => setToast({ tone: 'success', text })}
        />
      ) : null}
      {importing ? (
        <ImportTasksSheet
          onClose={() => setImporting(false)}
          onImported={(count) =>
            setToast({ tone: 'success', text: `Импортировано задач: ${count}` })
          }
        />
      ) : null}
      {selectedTask ? (
        <TaskDetailSheet
          task={selectedTask}
          isOwner={isOwner}
          markLoading={markDone.isPending && markDone.variables === selectedTask.id}
          markBusy={markDone.isPending}
          onClose={() => setSelectedTaskId(null)}
          onDone={() => handleDone(selectedTask)}
          onCancel={() => {
            const logId = myPendingLogByTask.get(selectedTask.id);
            if (logId !== undefined) handleCancel(logId);
          }}
          myPendingLogId={myPendingLogByTask.get(selectedTask.id) ?? null}
          cancelLoading={
            cancelLog.isPending && cancelLog.variables === myPendingLogByTask.get(selectedTask.id)
          }
          onEdit={() => {
            setEditingTaskId(selectedTask.id);
            setSelectedTaskId(null);
          }}
          onDelete={() => {
            setDeletingTaskId(selectedTask.id);
            setSelectedTaskId(null);
          }}
        />
      ) : null}
      {editingTask ? (
        <TaskFormSheet
          task={editingTask}
          onClose={() => setEditingTaskId(null)}
          onSaved={(text) => setToast({ tone: 'success', text })}
        />
      ) : null}
      {deletingTask ? (
        <DeleteTaskSheet
          task={deletingTask}
          onClose={() => setDeletingTaskId(null)}
          onDeleted={() => {
            setToast({ tone: 'success', text: 'Задача удалена' });
            setDeletingTaskId(null);
          }}
        />
      ) : null}
    </Screen>
  );
}
