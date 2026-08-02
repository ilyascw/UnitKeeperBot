import { useNavigate } from '@/routes/navigation';

import { useAuth } from '@/auth/useAuth';
import { routes } from '@/routes/paths';
import { Note, Screen } from '@/ui/kit';
import { EnterIcon, LogoIcon, PlusIcon } from '@/ui/icons';

/**
 * Landing for users without a group. Offers the two entry points: create a
 * brand-new group (becoming its owner) or join an existing one by name + code.
 * Replaces the legacy `/start` + `/create_group` + `/join_group` flow.
 */
export function OnboardingScreen() {
  const navigate = useNavigate();
  const { context } = useAuth();
  const name = context?.user?.first_name ?? context?.user?.username ?? null;

  return (
    <Screen>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 18,
          marginTop: 22,
          textAlign: 'center',
        }}
      >
        <div className="uk-logo" style={{ width: 80, height: 80, borderRadius: 24 }}>
          <LogoIcon size={38} style={{ color: 'var(--uk-on-accent)' }} strokeWidth={2.1} />
        </div>
        <div>
          <div style={{ font: "800 27px 'Manrope'", marginBottom: 8 }}>
            Привет{name ? `, ${name}` : ''} 👋
          </div>
          <div
            style={{
              font: "400 15px/1.6 'Manrope'",
              color: 'var(--uk-ink-70)',
              maxWidth: 290,
              marginInline: 'auto',
            }}
          >
            UnitKeeper помогает группе честно делить повторяющиеся дела и вести общий учёт.
          </div>
        </div>
      </div>

      <div className="uk-stack" style={{ marginTop: 6 }}>
        <button
          type="button"
          onClick={() => navigate(routes.onboardingCreate)}
          style={{
            padding: 20,
            borderRadius: 22,
            textAlign: 'left',
            cursor: 'pointer',
            background: 'var(--uk-accent-soft)',
            border: '1px solid rgba(124,166,217,.28)',
            boxShadow: 'inset 0 1px 0 rgba(255,255,255,.16)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div
              style={{
                width: 44,
                height: 44,
                flex: 'none',
                borderRadius: 14,
                display: 'grid',
                placeItems: 'center',
                background: 'rgba(255,255,255,.14)',
              }}
            >
              <PlusIcon size={22} style={{ color: '#eafcff' }} />
            </div>
            <div>
              <div style={{ font: "700 17px 'Manrope'" }}>Создать группу</div>
              <div style={{ font: "400 13px 'Manrope'", color: 'var(--uk-ink-70)' }}>
                Вы станете владельцем
              </div>
            </div>
          </div>
        </button>

        <button
          type="button"
          onClick={() => navigate(routes.onboardingJoin)}
          className="uk-card"
          style={{ padding: 20, textAlign: 'left', cursor: 'pointer', borderRadius: 22 }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div
              style={{
                width: 44,
                height: 44,
                flex: 'none',
                borderRadius: 14,
                display: 'grid',
                placeItems: 'center',
                background: 'rgba(255,255,255,.08)',
              }}
            >
              <EnterIcon size={22} style={{ color: 'var(--uk-blue)' }} />
            </div>
            <div>
              <div style={{ font: "700 17px 'Manrope'" }}>Вступить по коду</div>
              <div style={{ font: "400 13px 'Manrope'", color: 'var(--uk-ink-70)' }}>
                Нужны название и код
              </div>
            </div>
          </div>
        </button>
      </div>

      <div className="uk-spacer" />
      <Note tone="info">
        Код вступления выдаёт владелец группы. Спросите его у того, кто вас пригласил.
      </Note>
    </Screen>
  );
}
