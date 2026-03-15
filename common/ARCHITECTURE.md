# UnitKeeper Common Schema Notes

## What Was Preserved

- Users are independent from groups.
- Groups keep an owner, sprint start weekday, sprint duration, and group-level balance.
- Group membership remains explicit and supports leave and ownership handover flows.
- Tasks belong to a single group and are soft-deleted instead of physically removed.
- Task execution logs preserve the `pending` and `completed` flow and add an explicit `rejected` state for auditability.
- Personal balances remain stored per user per group.
- Sprint closing keeps enough persistent data to compute plan, fact, bonuses, balance deltas, and owner/member reports.

## What Was Normalized

- Legacy `Group.weights` JSON was replaced by `group_memberships` plus `group_member_weights`.
- The ambiguous `group_balance` vs `balance` behavior was normalized to a single `groups.balance` field.
- Transfer and sprint settlement mutations now have an explicit `balance_transactions` ledger instead of only mutating current balances.
- Sprint closing now has `sprint_runs` and `sprint_member_results` instead of recomputing everything from ad hoc logs only.
- Telegram profile fields are optional cached columns on `users`, while `id` remains the Telegram user id for migration compatibility.

## Intentional Deviations From Legacy

- Weekdays are stored as a strict enum (`monday` ... `sunday`) instead of Russian free-form strings.
- Workload weights allow decimal percentages at the storage layer, although current product intent still expects totals to sum to 100.
- Task logs keep approval metadata and rejection reason so backend and bot can provide a clean approval inbox later.
- Membership history is retained via `left_at`, with a partial unique index enforcing only one active membership per user.

## Deferred On Purpose

- No benefit shop, calendar sync, analytics marts, or export subsystem.
- No separate invitation entity yet; joining still maps to group name plus secret/password semantics.
- No backend use-case orchestration in this package.
- No seed dataset or demo fixtures; `common` only owns schema and persistence primitives.
