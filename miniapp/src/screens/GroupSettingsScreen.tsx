import { useEffect, useState, type FormEvent } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';

import { useUpdateGroupSettings } from '@/api/mutations';
import { useCurrentGroup } from '@/api/queries';
import { WEEKDAYS, type Weekday } from '@/api/types';
import { useAuth } from '@/auth/useAuth';
import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';
import { routes } from '@/routes/paths';
import { formatDay, WEEKDAY_SHORT } from '@/ui/format';
import {
  Button,
  Field,
  Note,
  Screen,
  ScreenHeader,
  Segmented,
  Stepper,
  TextInput,
} from '@/ui/kit';
import { RefreshIcon } from '@/ui/icons';

const WEEKDAY_OPTIONS = WEEKDAYS.map((day) => ({ value: day, label: WEEKDAY_SHORT[day] }));

function generateCode(): string {
  return Math.random().toString(36).slice(2, 10);
}

/**
 * Owner-only screen to edit join code, sprint start weekday and sprint
 * duration. Mirrors the legacy `/group_settings` handler. Non-owners are
 * redirected to the group surface so the route is safe to deep-link to.
 */
export function GroupSettingsScreen() {
  const navigate = useNavigate();
  const { context } = useAuth();
  const { data: group, isPending, isError, error, refetch } = useCurrentGroup();
  const mutation = useUpdateGroupSettings();

  const [secret, setSecret] = useState('');
  const [weekday, setWeekday] = useState<Weekday>('monday');
  const [duration, setDuration] = useState(7);

  // Hydrate inputs once the group card arrives — we can't init from a query
  // that may still be pending, so do it in an effect keyed on the group id.
  useEffect(() => {
    if (!group) return;
    setSecret(group.join_secret ?? '');
    setWeekday(group.sprint_start_weekday as Weekday);
    setDuration(group.sprint_duration_days);
  }, [group?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (isPending) return <Loader title="Загружаем настройки…" />;
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

  const isOwner = context?.user?.id === group.owner_user_id;
  if (!isOwner) return <Navigate to={routes.group} replace />;

  const changed =
    secret !== (group.join_secret ?? '') ||
    weekday !== group.sprint_start_weekday ||
    duration !== group.sprint_duration_days;

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    if (!changed || secret.trim().length < 3) return;
    mutation.mutate(
      {
        join_secret: secret !== group.join_secret ? secret : undefined,
        sprint_start_weekday:
          weekday !== group.sprint_start_weekday ? weekday : undefined,
        sprint_duration_days:
          duration !== group.sprint_duration_days ? duration : undefined,
      },
      { onSuccess: () => navigate(routes.group) },
    );
  };

  return (
    <Screen>
      <ScreenHeader title="Настройки группы" onBack={() => navigate(routes.group)} />
      <form onSubmit={handleSubmit} className="uk-stack" style={{ flex: 1 }}>
        <div className="uk-eyebrow">Доступ</div>
        <Field
          label="Код вступления"
          hint="Смена кода не выкинет текущих участников — старый код просто перестанет работать."
        >
          <div style={{ display: 'flex', gap: 8 }}>
            <TextInput
              value={secret}
              style={{ letterSpacing: '0.12em' }}
              onChange={(e) => setSecret(e.currentTarget.value)}
              disabled={mutation.isPending}
            />
            <button
              type="button"
              className="uk-icon-btn"
              aria-label="Сгенерировать новый код"
              onClick={() => setSecret(generateCode())}
              disabled={mutation.isPending}
            >
              <RefreshIcon size={20} />
            </button>
          </div>
        </Field>

        <div className="uk-divider" />

        <div className="uk-eyebrow">Период учёта</div>
        <Field label="День начала">
          <Segmented
            options={WEEKDAY_OPTIONS}
            value={weekday}
            onChange={setWeekday}
            disabled={mutation.isPending}
          />
        </Field>
        <Stepper
          label="Длительность"
          sublabel="7–28 дней, шаг 7"
          value={duration}
          suffix="дн"
          min={7}
          max={28}
          step={7}
          onChange={setDuration}
          disabled={mutation.isPending}
        />

        <Note tone="warn">
          Изменение периода применится со следующего спринта. Текущий период до{' '}
          {formatDay(group.sprint_period_end)} не изменится.
        </Note>

        {mutation.isError ? <Note tone="error">{mutation.error.message}</Note> : null}

        <div className="uk-spacer" />
        <Button
          type="submit"
          variant="primary"
          loading={mutation.isPending}
          disabled={!changed || secret.trim().length < 3}
        >
          Сохранить
        </Button>
        <Button
          type="button"
          variant="ghost"
          onClick={() => navigate(routes.group)}
          disabled={mutation.isPending}
        >
          Отменить
        </Button>
      </form>
    </Screen>
  );
}
