import { useNavigate } from 'react-router-dom';

import { routes } from '@/routes/paths';
import { Button, Screen } from '@/ui/kit';

export function NotFoundScreen() {
  const navigate = useNavigate();
  return (
    <Screen centered>
      <div
        style={{
          font: "800 96px/1 'Manrope'",
          background: 'linear-gradient(150deg,#5ee0d0,#7a86ff)',
          WebkitBackgroundClip: 'text',
          backgroundClip: 'text',
          color: 'transparent',
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
