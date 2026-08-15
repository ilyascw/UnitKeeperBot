## Why

Sprints settle at the *start* of their final day instead of after that day ends. The scheduler runs at `00:05 UTC` and treats a group as due when `window.period_end == today` (`application/jobs/sprint_close.py:52`), so balances are written while the Mini App still shows one remaining day and still accepts completions. Progress keeps changing after the numbers are frozen.

This is confirmed in production: all four groups had the `2026-08-03..2026-08-09` window closed at `2026-08-09 00:05 UTC` — 03:05 Moscow time on the last day, roughly 21 hours early. Every group runs `Europe/Moscow`, so the UTC-only assumption is wrong for the entire current user base, and the next close (`2026-08-16`) would repeat it.

## What Changes

- Sprint windows are evaluated in each group's stored IANA `timezone` instead of UTC. "Today", window boundaries, and log-query bounds all derive from group-local time.
- A window becomes closable only once it has **fully ended** in group-local time — i.e. after `period_end + 1 day` at 00:00 local. **BREAKING** for closure timing: a group in `Europe/Moscow` now settles 3 hours after local midnight rather than 21 hours before the day ends.
- The scheduler runs every 5 minutes instead of once daily at `00:05 UTC`, so groups across timezones each close near their own local boundary.
- Closure discovers *ended, unclosed* windows rather than assuming the current one. After scheduler downtime, missed windows are closed in chronological order, each settled with its own logs.
- Manual and scheduled closure of a window that is still active is rejected. Duplicate-close protection is preserved.
- Pending-log auto-reject is scoped to logs belonging to the window being closed, so a mark made in the next sprint is no longer rejected by the previous sprint's closure.
- `timezone` is validated as a real IANA zone on group creation. An unusable stored value falls back to UTC with a logged warning rather than stalling the group.

Assumptions recorded for review (not settled by the issue text):
- **Catch-up closes every missed window, oldest first.** The issue says "close the latest fully ended window"; taken literally, earlier missed windows would never settle and their balances would silently vanish. Chronological catch-up keeps balance history whole. Members may receive several reports at once after a long outage.
- **The schema default for `timezone` stays `'UTC'`.** `CreateGroupScreen.tsx:34` already sends `Intl.DateTimeFormat().resolvedOptions().timeZone`, so the default only applies when `Intl` is unavailable, where a neutral fallback is more honest than guessing Moscow.

Out of scope, tracked separately:
- Editing a group's timezone after creation (no UI exists today) — to be filed as its own issue. Client-side auto-detection already works.
- The one-off production data fix for the prematurely settled `2026-08-03..2026-08-09` sprint, and the post-deploy "bug fixed, go mark your tasks" broadcast. Both are operational steps listed in `tasks.md`, not behavior.

## Capabilities

### New Capabilities
- `sprint-closing`: when a sprint window is considered ended, which window a scheduled or manual close settles, how group-local time defines those boundaries, and how missed windows are caught up.

### Modified Capabilities
<!-- None: openspec/specs/ is empty, this is the first change in the repo. -->

## Impact

**Domain**
- `domain/services/sprint_math.py` — `SprintWindow.starts_at` / `ends_before` hardcode `timezone.utc`; `current_sprint_window` takes a bare `today: date`.

**Application** — all five `current_sprint_window` call sites need the group's zone:
- `application/jobs/sprint_close.py` — `list_due_group_ids` due-ness check and window selection
- `application/sprints/service.py:47` (`get_temp_results`), `:136` (`close_current_sprint`, incl. pending-log reject at `:161`)
- `application/groups/service.py:163` — `sprint_ends_at` sent to the Mini App
- `application/tasks/service.py:490`

**Entrypoint**
- `entrypoints/scheduler.py:73` — `SPRINT_CLOSE_CRON` daily → 5-minute interval; module docstring and the stale comment at `:70-72` (which describes `period_end == yesterday`, contradicting the code) both need correcting.

**API**
- `api/schemas/groups.py:14` — `timezone` accepts any 1–64 char string; needs IANA validation.
- No response-shape change. `sprint_ends_at` keeps its type, but its value shifts to the group-local boundary.

**Data**
- No migration. `groups.timezone` (`varchar(64) not null default 'UTC'`) and timezone-aware `sprint_ends_at` already exist.

**Deployment**
- Backend and scheduler must ship from the same image.
