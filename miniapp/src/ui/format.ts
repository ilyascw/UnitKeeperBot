import type { Weekday } from '@/api/types';

export const WEEKDAY_SHORT: Record<Weekday, string> = {
  monday: 'Пн',
  tuesday: 'Вт',
  wednesday: 'Ср',
  thursday: 'Чт',
  friday: 'Пт',
  saturday: 'Сб',
  sunday: 'Вс',
};

export const WEEKDAY_LONG: Record<Weekday, string> = {
  monday: 'Понедельник',
  tuesday: 'Вторник',
  wednesday: 'Среда',
  thursday: 'Четверг',
  friday: 'Пятница',
  saturday: 'Суббота',
  sunday: 'Воскресенье',
};

/** "старт по понедельникам" wording for the sprint cadence. */
export const WEEKDAY_EVERY: Record<Weekday, string> = {
  monday: 'по понедельникам',
  tuesday: 'по вторникам',
  wednesday: 'по средам',
  thursday: 'по четвергам',
  friday: 'по пятницам',
  saturday: 'по субботам',
  sunday: 'по воскресеньям',
};

/** Currency-style glyph for "units" (юниты), shown after amounts. */
export const UNIT_SYMBOL = 'Ⓤ';

const DAY_FMT = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long' });

/** Formats an ISO date/datetime as `6 июля`, tolerating bad input. */
export function formatDay(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : DAY_FMT.format(date);
}

/** `6 – 12 июля` for the current sprint window. */
export function formatPeriod(startIso: string, endIso: string): string {
  return `${formatDay(startIso)} – ${formatDay(endIso)}`;
}

/** Whole days remaining until the given instant, floored at 0. */
export function daysUntil(iso: string): number {
  const end = new Date(iso).getTime();
  if (Number.isNaN(end)) return 0;
  const diff = end - Date.now();
  return Math.max(0, Math.ceil(diff / 86_400_000));
}

function plural(n: number, one: string, few: string, many: string): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return few;
  return many;
}

/** Russian pluralisation for "день / дня / дней". */
export function pluralDays(n: number): string {
  return `${n} ${plural(n, 'день', 'дня', 'дней')}`;
}

/** "остался 1 день", "осталось 2 дня" — verb agrees in gender/number with "день". */
export function daysLeftLabel(n: number): string {
  const verb = n % 10 === 1 && n % 100 !== 11 ? 'остался' : 'осталось';
  return `${verb} ${pluralDays(n)}`;
}

/** Russian pluralisation for "участник / участника / участников". */
export function pluralMembers(n: number): string {
  return `${n} ${plural(n, 'участник', 'участника', 'участников')}`;
}

/** CSS colour for a signed unit balance: pink for debt, mint for surplus. */
export function balanceColor(value: string): string {
  const n = Number.parseFloat(value);
  if (Number.isFinite(n) && n < 0) return 'var(--uk-danger-soft)';
  if (Number.isFinite(n) && n > 0) return 'var(--uk-positive)';
  return 'var(--uk-ink)';
}

/** `-5.95` → `−5.95`, `18.4` → `+18.40`; a clean signed unit balance. */
export function formatBalance(value: string): string {
  const n = Number.parseFloat(value);
  if (!Number.isFinite(n)) return value;
  const fixed = Math.abs(n).toFixed(2);
  if (n < 0) return `−${fixed}`;
  if (n > 0) return `+${fixed}`;
  return fixed;
}

/** Trims a decimal string for display: `5.00` → `5`, `2.50` → `2.5`. */
export function formatUnits(value: string): string {
  const n = Number.parseFloat(value);
  if (!Number.isFinite(n)) return value;
  return String(Math.round(n * 100) / 100);
}

/** A member's display name with graceful fallbacks. */
export function memberName(m: {
  first_name: string | null;
  username: string | null;
  user_id: number;
}): string {
  return m.first_name ?? m.username ?? `Участник ${m.user_id}`;
}
