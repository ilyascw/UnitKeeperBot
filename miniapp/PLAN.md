# Miniapp Plan

## Goal
- Make the miniapp the main user interface for UnitKeeper.
- Cover all daily workflows that currently live in the legacy bot, except pure notifications.

## Scope
- Authentication via Telegram Mini App init data.
- Main dashboard, task workflows, balances, group settings, sprint progress.
- Native Telegram UI Kit look and feel.
- Chosen stack: Vite + React + TypeScript + Telegram UI Kit.

## Phase 1: Foundation
- [x] Choose frontend stack: Vite + React + TypeScript + Telegram UI Kit.
- [x] Bootstrap the app shell around Telegram Mini Apps.
- [x] Set up routing, layout, design tokens, and Telegram UI Kit integration.
- [x] Add API client, auth bootstrap from init data, error boundary, and loading states.
- [ ] Define screen-level contract with backend before writing business UI.

## Phase 2: Core Screens
- [x] Onboarding screen with create group and join group actions.
- [ ] Dashboard with current sprint summary, personal balance, and pending approvals count.
- [x] Group screen with group info, members, weights, owner marker, and sprint settings.
- [x] Task catalog screen with active tasks, remaining executions, and task details.
- [x] Task management screen for add, edit, soft-delete, and quick frequency adjustments.
- [ ] Balance screen with current balance, transfer flow, and transfer history placeholder.
- [ ] Sprint progress screen with plan vs fact, completed tasks, and progress visualization.

## Phase 3: Product Flows
- [x] Create group flow with name, password, start weekday, and sprint duration.
- [x] Join group flow with group name and password.
- [x] Leave group flow with explicit confirmation and owner handover UX.
- [x] Add single task flow.
- [x] Bulk task import flow using pasted tabular data.
- [x] Execute task flow with pending approval state.
- [x] Review pending approvals inside the miniapp inbox.
- [ ] Unit transfer flow with recipient picker and amount validation.
- [x] Group settings flow for owner-only actions.

## Phase 4: UX Hardening
- [ ] Add empty states for no group, no tasks, no balances, and no pending approvals.
- [ ] Add deep-link entry points from bot notifications into exact miniapp screens.
- [ ] Handle reconnect, expired auth, and partial API failures gracefully.
- [ ] Make mobile layout the default and verify Telegram in-app browser behavior.

## Legacy Coverage
- [x] `/start`
- [x] `/create_group`
- [x] `/join_group`
- [x] `/exit_group`
- [x] `/group_info`
- [x] `/group_settings`
- [ ] `/add_task`
- [ ] `/edit_task`
- [ ] `/delete_task`
- [ ] `/list_of_tasks`
- [ ] `/tasks`
- [ ] `/temp_results`
- [ ] `/balance`
- [ ] `/about`

## Deferred For Later
- [ ] Full notification center parity if bot approvals are enough for v1.
- [ ] Benefit shop.
- [ ] Calendar integrations.
