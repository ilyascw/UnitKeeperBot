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

/** Russian pluralisation for "участник / участника / участников". */
export function pluralMembers(n: number): string {
  return `${n} ${plural(n, 'участник', 'участника', 'участников')}`;
}
