import { useState, type FormEvent } from 'react';
import { useNavigate } from '@/routes/navigation';

import { useCreateGroup } from '@/api/mutations';
import { WEEKDAYS, type Weekday } from '@/api/types';
import { routes } from '@/routes/paths';
import { WEEKDAY_SHORT } from '@/ui/format';
import {
  Button,
  Field,
  Note,
  Screen,
  ScreenHeader,
  Segmented,
  Stepper,
  TextInput,
} from '@/components/ui/app-kit';

const WEEKDAY_OPTIONS = WEEKDAYS.map((day) => ({ value: day, label: WEEKDAY_SHORT[day] }));

/**
 * Owner-driven flow to create a brand-new group. Mirrors legacy `/create_group`
 * but validates on the backend and immediately routes the new owner to the
 * group surface on success.
 */
export function CreateGroupScreen() {
  const navigate = useNavigate();
  const mutation = useCreateGroup();

  const [name, setName] = useState('');
  const [secret, setSecret] = useState('');
  const [weekday, setWeekday] = useState<Weekday>('monday');
  const [duration, setDuration] = useState(7);
  const timezone =
    typeof Intl !== 'undefined' ? Intl.DateTimeFormat().resolvedOptions().timeZone : 'UTC';

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    if (disabled) return;
    mutation.mutate(
      {
        name: name.trim(),
        join_secret: secret,
        sprint_start_weekday: weekday,
        sprint_duration_days: duration,
        timezone,
      },
      { onSuccess: () => navigate(routes.group, { replace: true }) },
    );
  };

  const disabled = mutation.isPending || name.trim().length === 0 || secret.length < 3;

  return (
    <Screen>
      <ScreenHeader title="Новая группа" onBack={() => navigate(routes.onboarding)} />
      <form onSubmit={handleSubmit} className="uk-stack" style={{ flex: 1 }}>
        <Field label="Название группы">
          <TextInput
            placeholder="Например: Квартира на Лесной"
            value={name}
            onChange={(e) => setName(e.currentTarget.value)}
            disabled={mutation.isPending}
          />
        </Field>

        <Field
          label="Код вступления"
          hint="Передайте его тем, кого хотите пригласить. Можно поменять позже в настройках."
        >
          <TextInput
            placeholder="Минимум 3 символа"
            value={secret}
            style={{ letterSpacing: '0.12em' }}
            onChange={(e) => setSecret(e.currentTarget.value)}
            disabled={mutation.isPending}
          />
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

        <Note tone="info">
          Период — это отрезок, за который считаются план и балансы. Часовой пояс возьмём из вашего
          устройства.
        </Note>

        {mutation.isError ? <Note tone="error">{mutation.error.message}</Note> : null}

        <div className="uk-spacer" />
        <Button type="submit" variant="primary" loading={mutation.isPending} disabled={disabled}>
          Создать группу
        </Button>
      </form>
    </Screen>
  );
}
