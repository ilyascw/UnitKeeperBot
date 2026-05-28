import { Button, Placeholder } from '@telegram-apps/telegram-ui';
import { useNavigate } from 'react-router-dom';

import { routes } from '@/routes/paths';

export function NotFoundScreen() {
  const navigate = useNavigate();
  return (
    <div style={{ minHeight: '80vh', display: 'flex', alignItems: 'center' }}>
      <Placeholder header="Screen not found" description="This page doesn’t exist.">
        <Button size="m" onClick={() => navigate(routes.home, { replace: true })}>
          Go home
        </Button>
      </Placeholder>
    </div>
  );
}
