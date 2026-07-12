import type { ComponentType } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { routes, type RoutePath } from '@/routes/paths';
import { ChartIcon, CoinIcon, GroupIcon, HomeIcon, TasksIcon } from '@/ui/icons';

interface Tab {
  to: RoutePath;
  label: string;
  Icon: ComponentType<{ size?: number }>;
}

/** The five in-group sections, in the order shown in the design's tab bar. */
const TABS: Tab[] = [
  { to: routes.dashboard, label: 'Главная', Icon: HomeIcon },
  { to: routes.tasks, label: 'Задачи', Icon: TasksIcon },
  { to: routes.progress, label: 'Прогресс', Icon: ChartIcon },
  { to: routes.balance, label: 'Баланс', Icon: CoinIcon },
  { to: routes.group, label: 'Группа', Icon: GroupIcon },
];

/**
 * Floating glass tab bar for the daily-work sections. Rendered by the tabbed
 * layout so it stays fixed while the section screen above it scrolls.
 */
export function TabBar() {
  const navigate = useNavigate();
  const { pathname } = useLocation();

  return (
    <nav className="uk-tabbar" aria-label="Разделы">
      {TABS.map(({ to, label, Icon }) => {
        const active = pathname === to || pathname.startsWith(`${to}/`);
        return (
          <button
            key={to}
            type="button"
            className={`uk-tabbar__item${active ? ' uk-tabbar__item--active' : ''}`}
            aria-current={active ? 'page' : undefined}
            onClick={() => (active ? undefined : navigate(to))}
          >
            <span className="uk-tabbar__icon">
              <Icon size={23} />
            </span>
            <span>{label}</span>
          </button>
        );
      })}
    </nav>
  );
}
