import { Component, type ErrorInfo, type ReactNode } from 'react';

import { ErrorState } from './ErrorState';

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

/**
 * Top-level error boundary: catches render-time crashes anywhere in the tree
 * and shows a recoverable error screen instead of a blank white page.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('[error-boundary] uncaught error', error, info.componentStack);
  }

  private readonly handleReset = (): void => {
    this.setState({ error: null });
  };

  render(): ReactNode {
    if (this.state.error) {
      return (
        <ErrorState
          title="Что-то пошло не так"
          description={this.state.error.message}
          accent="rgba(217,118,124"
          onRetry={this.handleReset}
          retryLabel="Перезагрузить"
        />
      );
    }
    return this.props.children;
  }
}
