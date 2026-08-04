import { useNavigate } from '@/routes/navigation';

import { Button, Screen } from '@/components/ui/app-kit';
import { routes } from '@/routes/paths';

export function NotFoundScreen() {
  const navigate = useNavigate();
  return (
    <Screen centered>
      <div
        style={{
          font: "800 96px/1 'Manrope'",
          color: 'var(--uk-accent)',
        }}
      >
        404
      </div>
      <div>
        <div style={{ font: "700 22px 'Manrope'", marginBottom: 10 }}>Такой страницы нет</div>
        <div
          style={{
            font: "400 15px/1.6 'Manrope'",
            color: 'var(--uk-ink-70)',
            maxWidth: 260,
            marginInline: 'auto',
          }}
        >
          Возможно, ссылка устарела. Вернитесь на главную или откройте приложение из бота заново.
        </div>
      </div>
      <div style={{ width: '100%', maxWidth: 260, marginTop: 6 }}>
        <Button variant="primary" onClick={() => navigate(routes.home, { replace: true })}>
          На главную
        </Button>
      </div>
    </Screen>
  );
}
