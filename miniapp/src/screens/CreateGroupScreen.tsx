import { Button, Input, List, Section, Select } from '@telegram-apps/telegram-ui';
import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';

import { useCreateGroup } from '@/api/mutations';
import { WEEKDAYS, type Weekday } from '@/api/types';
import { routes } from '@/routes/paths';

const WEEKDAY_LABEL: Record<Weekday, string> = {
  monday: 'Понедельник',
  tuesday: 'Вторник',
  wednesday: 'Среда',
  thursday: 'Четверг',
  friday: 'Пятница',
  saturday: 'Суббота',
  sunday: 'Воскресенье',
};

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
  const [duration, setDuration] = useState('7');
  const timezone =
    typeof Intl !== 'undefined' ? Intl.DateTimeFormat().resolvedOptions().timeZone : 'UTC';

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    const days = Number.parseInt(duration, 10);
    if (!Number.isFinite(days) || days <= 0) return;
    mutation.mutate(
      {
        name: name.trim(),
        join_secret: secret,
        sprint_start_weekday: weekday,
        sprint_duration_days: days,
        timezone,
      },
      { onSuccess: () => navigate(routes.group, { replace: true }) },
    );
  };

  const disabled =
    mutation.isPending || name.trim().length === 0 || secret.length < 3 || duration.length === 0;

  return (
    <form onSubmit={handleSubmit}>
      <List>
        <Section
          header="Создание группы"
          footer="Код нужен другим участникам для вступления в группу."
        >
          <Input
            header="Название группы"
            placeholder="Например: Семья"
            value={name}
            onChange={(event) => setName(event.currentTarget.value)}
            disabled={mutation.isPending}
          />
          <Input
            header="Код вступления"
            placeholder="Минимум 3 символа"
            value={secret}
            onChange={(event) => setSecret(event.currentTarget.value)}
            disabled={mutation.isPending}
          />
        </Section>
        <Section header="Период учёта" footer="Период начинается заново в выбранный день недели.">
          <Select
            header="День начала"
            value={weekday}
            onChange={(event) => setWeekday(event.currentTarget.value as Weekday)}
            disabled={mutation.isPending}
          >
            {WEEKDAYS.map((day) => (
              <option key={day} value={day}>
                {WEEKDAY_LABEL[day]}
              </option>
            ))}
          </Select>
          <Input
            header="Длительность в днях"
            type="number"
            inputMode="numeric"
            value={duration}
            onChange={(event) => setDuration(event.currentTarget.value)}
            disabled={mutation.isPending}
          />
        </Section>
        {mutation.isError ? (
          <Section header="Не удалось создать группу">
            <div style={{ padding: '8px 16px', color: 'var(--tgui--destructive_text_color)' }}>
              {mutation.error.message}
            </div>
          </Section>
        ) : null}
        <Section>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: '8px 16px' }}>
            <Button type="submit" stretched size="l" loading={mutation.isPending} disabled={disabled}>
              Создать группу
            </Button>
            <Button
              type="button"
              stretched
              size="l"
              mode="plain"
              onClick={() => navigate(routes.onboarding)}
              disabled={mutation.isPending}
            >
              Отмена
            </Button>
          </div>
        </Section>
      </List>
    </form>
  );
}
