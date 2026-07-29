/* eslint-disable react-refresh/only-export-components */

import type { ReactNode } from 'react';
import { Redirect, useLocation as useWouterLocation } from 'wouter';

interface NavigateOptions {
  replace?: boolean;
}

type NavigateFunction = (to: string, options?: NavigateOptions) => void;

/**
 * Small application-level adapter around wouter. Screens depend on this
 * stable API instead of a router package directly.
 */
export function useNavigate(): NavigateFunction {
  const [, setLocation] = useWouterLocation();
  return (to, options) => {
    setLocation(to, { replace: options?.replace });
  };
}

export function useLocation(): { pathname: string } {
  const [pathname] = useWouterLocation();
  return { pathname };
}

export function Navigate({
  to,
  replace = false,
}: {
  to: string;
  replace?: boolean;
}): ReactNode {
  return <Redirect to={to} replace={replace} />;
}
