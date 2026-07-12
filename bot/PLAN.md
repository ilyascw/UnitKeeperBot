# Bot Plan

## Goal
- Make the bot thin.
- Bot should notify, route users into the miniapp, and cover minimal fallback interactions only.

## Scope
- `/start`, basic help, approval notifications, sprint reports, reminders, and deep links.

## Phase 1: Thin Bot Skeleton
- [x] Bootstrap bot app with clean router structure.
- [x] Connect bot to backend APIs or service layer, without embedding business rules in handlers.
- [x] Add shared configuration and startup lifecycle.

## Phase 2: Minimal User Surface
- [x] `/start` should identify the user and open the miniapp.
- [x] `/help` should explain the new product surface and available bot-only actions.
- [x] `/about` can stay as a lightweight educational fallback or link into miniapp content.
- [x] Add fallback message for commands that moved into the miniapp.

## Phase 3: Notification Workflows
- [x] Send task approval requests to other group members.
- [x] Let recipients approve or reject directly from bot actions.
- [x] Notify performer about approval result or rejection reason.
- [x] Send sprint summary notifications and personal reports.
- [x] Send reminders about pending approvals, unfinished sprint, and critical group events.

## Phase 4: Operational Flows
- [x] Support owner handover prompts when a group owner leaves.
- [x] Support deep links into exact miniapp screens for each notification type.
- [x] Keep minimal admin or recovery actions if a miniapp flow is temporarily unavailable.

## Explicit Non-Goals
- [x] No full CRUD UX for tasks in the bot by default.
- [x] No heavy FSM flows if the miniapp can do the job better.
- [x] No duplicated sprint math or balance logic in handlers.

## Legacy Mapping
- [x] Keep `/start`, `/help`, `/about` in some form.
- [x] Keep approval and rejection flows from [`UnitKeeperBot/handlers/tasks.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/tasks.py)
- [x] Keep sprint result delivery from [`UnitKeeperBot/sprint_results.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/sprint_results.py)
- [x] Move the rest of interactive product flows into the miniapp
