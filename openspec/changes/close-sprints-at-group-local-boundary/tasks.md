## 1. Timezone plumbing

- [x] 1.1 Add a helper that resolves a group's stored timezone to a `ZoneInfo`, returning UTC and logging a warning (with the group id) when the value is unusable
- [x] 1.2 Add IANA validation to the group-creation timezone field in `api/schemas/groups.py` so unknown identifiers are rejected with a validation error
- [x] 1.3 Decide the fate of `Clock.today()` in `application/ports.py`: remove it, or rename it so its UTC-only meaning is explicit; update `UtcClock` accordingly

## 2. Zone-aware sprint windows

- [x] 2.1 Make `SprintWindow` carry the group's zone and derive `starts_at` / `ends_before` from it instead of hardcoding `timezone.utc`
- [x] 2.2 Change `current_sprint_window` to take the zone (and an instant rather than a bare `today`), deriving the local date internally
- [x] 2.3 Add an `ends_before`-based predicate for "this window has fully ended as of instant N"
- [x] 2.4 Unit-test window bounds for a `Europe/Moscow` group, including the exact `00:00` local boundary belonging to the next window
- [x] 2.5 Unit-test window bounds across a DST transition in a zone that observes it, covering the 23- and 25-hour local days

## 3. Update the five call sites

- [x] 3.1 `application/jobs/sprint_close.py:46` — pass the group's zone
- [x] 3.2 `application/sprints/service.py:47` (`get_temp_results`) — pass the group's zone
- [x] 3.3 `application/sprints/service.py:136` (`close_current_sprint`) — pass the group's zone
- [x] 3.4 `application/groups/service.py:163` — pass the group's zone and drop the manual UTC `datetime.combine` for `sprint_ends_at`
- [x] 3.5 `application/tasks/service.py:490` — pass the group's zone
- [x] 3.6 Verify no `current_sprint_window` call site is left deriving "today" from ambient UTC

## 4. Closure timing and window discovery

- [x] 4.1 Replace the `window.period_end != today` due-ness check in `list_due_group_ids` with `now >= window.ends_before`
- [x] 4.2 Implement backward discovery of ended windows with no `CLOSED` sprint run, bounded by a lookback cap and the group's `created_at`, logging when the cap is hit
- [x] 4.3 Settle discovered windows oldest-first, passing the exact period into the close use case rather than letting it recompute the current window
- [x] 4.4 Make `close_current_sprint` accept an explicit period and reject any window that has not ended locally, for both scheduled and manual callers
- [x] 4.5 Confirm the existing `CLOSED` sprint-run guard still short-circuits duplicate closes on the explicit-period path

## 5. Pending-log scoping

- [x] 5.1 Scope the pending-log auto-reject in `close_current_sprint` to logs whose `created_at` falls inside the window being settled
- [x] 5.2 Test that a pending mark created after the settled window survives a catch-up close and can still be approved

## 6. Scheduler

- [x] 6.1 Replace `SPRINT_CLOSE_CRON` in `entrypoints/scheduler.py:73` with a 5-minute interval trigger
- [x] 6.2 Rewrite the module docstring (`:8-12`) and the stale comment at `:70-72` — the latter currently describes `period_end == yesterday`, which the code never did
- [x] 6.3 Correct the timezone-policy docstring in `application/jobs/sprint_close.py:10-15`, which states per-group timezones are not consulted

## 7. Test coverage

- [x] 7.1 A `Europe/Moscow` group is not closed at `2026-08-16T00:05Z` and is closed on the first pass at or after `2026-08-16T21:00Z`
- [x] 7.2 Completions recorded at `23:30` local on the final day are counted in the settlement
- [x] 7.3 Two windows missed during downtime are settled oldest-first, each with only its own completions
- [x] 7.4 Repeated passes with no newly ended window settle nothing
- [x] 7.5 Manual close of a running window is rejected and mutates nothing
- [x] 7.6 A group with an unresolvable stored timezone falls back to UTC, logs a warning, and does not block other groups in the same pass

## 8. Release

- [x] 8.1 Update the documented UTC-only limitation in `AGENTS.md` / `architecture.md` wherever it is stated
- [ ] 8.2 Deploy backend and scheduler from the same image
- [ ] 8.3 Verify the first post-deploy pass settles nothing (the `2026-08-10..2026-08-16` window is still open)
- [x] 8.4 One-off production data fix: zero out the prematurely settled `2026-08-03..2026-08-09` sprint and roll back the balances it wrote (groups 1 and 4, `-20.00` and `-8.00`) — confirm the exact statements with the user before running them. Applied 2026-08-15, preceded by `docs/backend/backfill-missing-opening-entry.sql` (see #37) without which the per-user reconciliation check could not pass
- [ ] 8.5 Manually broadcast the "bug is fixed, mark your tasks" message to group members
- [ ] 8.6 Watch the `2026-08-17T00:00+03:00` boundary and confirm closure lands within 5 minutes of it

## 9. Follow-ups (not part of this change)

- [x] 9.1 File an issue for editing a group's timezone after creation (settings UI + endpoint); note that client-side auto-detection already exists at `miniapp/src/screens/CreateGroupScreen.tsx:34`
- [x] 9.2 Ask whether the `invalid` label on issue #28 should be removed, given production data confirms the bug
