## Context

See `proposal.md` — Why. The constraints that shape the approach:

- `SprintWindow.starts_at` / `ends_before` (`domain/services/sprint_math.py:22-28`) build instants with `tzinfo=timezone.utc`. `current_sprint_window` takes a bare `today: date` with no zone attached, so a window is a pair of naive calendar dates that only becomes an instant at the very end.
- Five call sites pass `self._clock.today()` into `current_sprint_window`: `jobs/sprint_close.py:46`, `sprints/service.py:47` and `:136`, `groups/service.py:163`, `tasks/service.py:490`. All five inherit UTC today.
- `Clock` (`application/ports.py:31-34`) exposes `now()` and `today()`. `today()` is inherently zone-bound and is the root of the problem.
- Due-ness today is an equality test on dates (`window.period_end != today`), which is what makes closure fire on the first instant of the final day.
- `sprint_runs` has a row per `(group_id, period_start, period_end)` with a `status`; `close_current_sprint` already refuses to re-close a `CLOSED` row. That is the existing idempotency anchor and is worth keeping.
- `task_logs.created_at` is `timestamptz` and there is an index on `(group_id, status, created_at)` — scoping pending rejection to a window is cheap.
- Production runs four groups, all `Europe/Moscow`, all Monday/7-day. There is no multi-timezone traffic yet, so this is fixed before it becomes visible rather than in response to spread-out users.

## Goals / Non-Goals

**Goals:**
- Make the group's timezone the single source of truth for "what day is it" in all sprint math.
- Make closure a function of *elapsed time* ("has this window ended?") rather than *calendar equality* ("is today the last day?").
- Keep settlement arithmetic untouched — only timing and window selection move.

**Non-Goals:**
- Per-group scheduling. One frequent global pass that asks each group whether it is ready is simpler than per-group timers and is adequate at this scale.
- Reworking `sprint_runs` or adding a migration.
- Per-user timezones. The group is the settlement unit.

## Decisions

**Carry the zone into the window, not around it.** Give `current_sprint_window` the group's zone and let `SprintWindow` hold it, so `starts_at` / `ends_before` produce correct instants on their own. The alternative — converting at each of the five call sites — leaves five chances to forget, and the existing UTC-hardcoded properties would keep silently returning wrong instants. Making `SprintWindow` zone-aware means a call site that forgets to pass a zone fails loudly at construction rather than quietly settling at the wrong hour.

**Replace `Clock.today()` with an instant plus a zone.** `today()` cannot answer "which day is it" without knowing for whom. Callers should take `clock.now()` (already timezone-aware UTC) and derive the local date via the group's zone. This deletes the ambient-UTC assumption at its source instead of patching each reader. `UtcClock` keeps `now()`; `today()` either goes away or becomes explicitly UTC-only for non-group contexts.

**Due-ness is `now >= window.ends_before`, not `period_end == today`.** This is the actual fix. It is also what makes catch-up fall out for free: a window that ended three days ago still satisfies the comparison, so no special "we missed one" branch is needed.

**Discover windows by walking back from the current one.** To find unsettled ended windows, step backward from the group's current window while a window has ended and has no `CLOSED` sprint run, then settle forward from the oldest. Bound the walk (e.g. a few windows, or the group's `created_at`) so a group that has never closed does not replay its whole history. The alternative — querying for gaps in `sprint_runs` — needs the same window math anyway and is harder to reason about.

**5-minute interval, not a per-group cron.** With `now >= ends_before`, a group settles within 5 minutes of its local boundary regardless of zone. Worst-case lateness is the interval itself, which is invisible against a week-long sprint. `IntervalTrigger` also removes the "did we miss the daily 00:05 tick" failure mode entirely.

**Scope pending rejection by `created_at` within the window bounds.** Today `close_current_sprint` rejects *all* pending logs for the group (`sprints/service.py:161-175`), justified by a comment claiming nothing from the next window can exist yet. Catch-up breaks that assumption: settling an old window while a newer one is running would reject marks that legitimately belong to the newer one. The window bounds are already computed; reuse them.

**Validate IANA input at the API edge, fall back at the closure edge.** `zoneinfo.ZoneInfo(value)` raising is the validation. Rejecting bad input on write prevents new breakage; falling back to UTC on read means one corrupt legacy row cannot wedge the scheduler for every other group. Strict-everywhere was considered and rejected: a scheduler that refuses to run because of one bad row is a worse failure than one group settling in the wrong zone with a warning.

## Risks / Trade-offs

- **`sprint_ends_at` shifts for existing clients** → No shape change, and the value moves *later* (Moscow: `2026-08-16T00:00Z` → `2026-08-16T21:00Z`), so users gain time rather than losing it. Nothing to migrate.
- **The `2026-08-03..2026-08-09` sprint stays mis-settled** → Out of the code change; handled as a one-off data fix in `tasks.md`, decided with the user.
- **Catch-up could emit a burst of reports after a long outage** → Accepted. The outbox is already deduped by key. Losing balance history was judged worse than a batch of notifications.
- **Unbounded backward walk on a group that never closed** → Cap the lookback and log when the cap is hit, so a misconfigured group degrades visibly instead of replaying months of windows.
- **DST transitions make a local day 23 or 25 hours long** → Deriving instants through `ZoneInfo` rather than fixed offsets handles this. Moscow has no DST, so it is untested in production; boundary tests should cover a DST zone explicitly.
- **5-minute polling over all groups** → Trivial at four groups; the per-pass query is a bounded scan. Worth revisiting only at a much larger group count.
- **Backend and scheduler must ship together** → Same image, same deploy, as noted in the issue.

## Migration Plan

1. Deploy backend and scheduler from one image.
2. Confirm the first pass settles nothing (the `2026-08-10..2026-08-16` window is still open) — the expected quiet state.
3. Apply the one-off data fix for the prematurely settled sprint.
4. Broadcast the "bug is fixed, go mark your tasks" message manually.
5. Watch the `2026-08-17T00:00+03:00` boundary — closure should land within 5 minutes of it, not 21 hours early.

Rollback: revert the image. No schema change, so no down-migration. A sprint settled by the new logic stays settled; the old code would see it as `CLOSED` and skip it.
