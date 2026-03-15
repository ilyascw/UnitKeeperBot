# Bot Plan

## Goal
- Make the bot thin.
- Bot should notify, route users into the miniapp, and cover minimal fallback interactions only.

## Scope
- `/start`, basic help, approval notifications, sprint reports, reminders, and deep links.

## Phase 1: Thin Bot Skeleton
- [ ] Bootstrap bot app with clean router structure.
- [ ] Connect bot to backend APIs or service layer, without embedding business rules in handlers.
- [ ] Add shared configuration and startup lifecycle.

## Phase 2: Minimal User Surface
- [ ] `/start` should identify the user and open the miniapp.
- [ ] `/help` should explain the new product surface and available bot-only actions.
- [ ] `/about` can stay as a lightweight educational fallback or link into miniapp content.
- [ ] Add fallback message for commands that moved into the miniapp.

## Phase 3: Notification Workflows
- [ ] Send task approval requests to other group members.
- [ ] Let recipients approve or reject directly from bot actions.
- [ ] Notify performer about approval result or rejection reason.
- [ ] Send sprint summary notifications and personal reports.
- [ ] Send reminders about pending approvals, unfinished sprint, and critical group events.

## Phase 4: Operational Flows
- [ ] Support owner handover prompts when a group owner leaves.
- [ ] Support deep links into exact miniapp screens for each notification type.
- [ ] Keep minimal admin or recovery actions if a miniapp flow is temporarily unavailable.

## Explicit Non-Goals
- [ ] No full CRUD UX for tasks in the bot by default.
- [ ] No heavy FSM flows if the miniapp can do the job better.
- [ ] No duplicated sprint math or balance logic in handlers.

## Legacy Mapping
- [ ] Keep `/start`, `/help`, `/about` in some form.
- [ ] Keep approval and rejection flows from [`UnitKeeperBot/handlers/tasks.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/tasks.py)
- [ ] Keep sprint result delivery from [`UnitKeeperBot/sprint_results.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/sprint_results.py)
- [ ] Move the rest of interactive product flows into the miniapp
