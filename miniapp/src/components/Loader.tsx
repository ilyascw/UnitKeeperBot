import { BrandSpinner, Screen } from '@/ui/kit';

/** Centred full-height loading state with the brand spinner. */
export function Loader({
  title = 'Загружаем…',
  label,
}: {
  title?: string;
  label?: string;
}) {
  return (
    <Screen centered>
      <BrandSpinner />
      <div style={{ marginTop: 8 }}>
        <div style={{ font: "700 20px 'Manrope'", marginBottom: 6 }}>{title}</div>
        {label ? (
          <div
            style={{
              font: "400 15px/1.5 'Manrope'",
              color: 'var(--uk-ink-70)',
              maxWidth: 250,
              marginInline: 'auto',
            }}
          >
            {label}
          </div>
        ) : null}
      </div>
    </Screen>
  );
}
