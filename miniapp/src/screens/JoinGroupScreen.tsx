import { useState, type FormEvent } from 'react';
import { useNavigate } from '@/routes/navigation';

import { useJoinGroup } from '@/api/mutations';
import { routes } from '@/routes/paths';
import { Button, Field, Note, Screen, ScreenHeader, TextInput } from '@/ui/kit';

/**
 * Joins an existing group by name and code. Mirrors legacy `/join_group`.
 */
export function JoinGroupScreen() {
  const navigate = useNavigate();
  const mutation = useJoinGroup();

  const [name, setName] = useState('');
  const [secret, setSecret] = useState('');

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    if (disabled) return;
    mutation.mutate(
      { name: name.trim(), join_secret: secret },
      { onSuccess: () => navigate(routes.group, { replace: true }) },
    );
  };

  const disabled = mutation.isPending || name.trim().length === 0 || secret.length < 3;
  const invalid = mutation.isError;

  return (
    <Screen>
      <ScreenHeader title="Вступить в группу" onBack={() => navigate(routes.onboarding)} />
      <form onSubmit={handleSubmit} className="uk-stack" style={{ flex: 1 }}>
        <Note tone="info">
          Название группы и код вступления узнайте у того, кто вас пригласил.
        </Note>

        <Field label="Название группы">
          <TextInput
            placeholder="Квартира на Лесной"
            value={name}
            invalid={invalid}
            onChange={(e) => setName(e.currentTarget.value)}
            disabled={mutation.isPending}
          />
        </Field>

        <Field
          label="Код вступления"
          error={invalid ? 'Неверное название или код. Проверьте у владельца.' : undefined}
        >
          <TextInput
            placeholder="например: lesnaya-2026"
            value={secret}
            invalid={invalid}
            style={{ letterSpacing: '0.12em' }}
            onChange={(e) => setSecret(e.currentTarget.value)}
            disabled={mutation.isPending}
          />
        </Field>

        <div className="uk-spacer" />
        <Button type="submit" variant="primary" loading={mutation.isPending} disabled={disabled}>
          Вступить
        </Button>
        <Button
          type="button"
          variant="ghost"
          onClick={() => navigate(routes.onboarding)}
          disabled={mutation.isPending}
        >
          Назад
        </Button>
      </form>
    </Screen>
  );
}
