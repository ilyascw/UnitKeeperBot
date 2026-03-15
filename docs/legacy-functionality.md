# Legacy UnitKeeperBot Functional Map

## Status
- Legacy source of truth: [`UnitKeeperBot`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot)
- This artifact captures what is actually implemented in code, plus important mismatches against old descriptions.
- Migration rule: preserve behavior intentionally, but do not port legacy bugs as-is.

## Current Domain Model

### `Group`
- Fields: `id`, `name`, `password`, `start_day`, `sprint_duration`, `owner_id`, `group_balance`, `weights`
- `weights` is a JSON map `{user_id: percentage}`

### `User`
- Fields: `id`, `group_id`
- Telegram profile data is not stored locally; bot asks Telegram API when needed

### `Task`
- Fields: `id`, `group_id`, `title`, `frequency`, `cost`, `status`
- `status=False` means soft-deleted

### `Log`
- Fields: `id`, `group_id`, `user_id`, `task_id`, `status`, `timestamp`
- Used for task completion events with statuses `pending` and `completed`

### `Balance`
- Fields: `id`, `user_id`, `group_id`, `balance`

## Functional Inventory

| Legacy feature | Actual behavior in code | Entry points | Main files | Future home |
| --- | --- | --- | --- | --- |
| User bootstrap | `/start` creates a `User` if missing and offers create/join group actions | `/start` | [`UnitKeeperBot/handlers/start.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/start.py) | Bot + backend |
| Group creation | Creates group with unique name, password, sprint start day, sprint duration divisible by 7, owner, equalized weights, and zero balance record for creator | `/create_group`, `➕ Создать группу` | [`UnitKeeperBot/handlers/group.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/group.py) | Miniapp + backend |
| Group joining | Join by group name and password, attach user to group, create missing balance record, rebalance weights equally across members | `/join_group`, `🔑 Вступить в группу` | [`UnitKeeperBot/handlers/join_group.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/join_group.py) | Miniapp + backend |
| Group leaving | Leave group via confirmation code; remove user from weights; if owner leaves, ownership is reassigned manually or automatically | `/exit_group` | [`UnitKeeperBot/handlers/exit_group.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/exit_group.py) | Miniapp + backend, bot for notifications |
| Group info | Shows group metadata, sprint end date, group balance, members, weights, owner marker, member balances | `/group_info` | [`UnitKeeperBot/handlers/group_info.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/group_info.py) | Miniapp + backend |
| Group settings | Owner can change start day, password, sprint duration, and per-user weights | `/group_settings` | [`UnitKeeperBot/handlers/group_settings.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/group_settings.py) | Miniapp + backend |
| Add one task | Create a task with title, frequency, cost in the current group | `/add_task` | [`UnitKeeperBot/handlers/add_task.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/add_task.py) | Miniapp + backend |
| Bulk task import | Sends XLSX template, reads uploaded Excel from memory, validates columns and numeric values, creates multiple tasks | `/add_task` -> `Множество задач` | [`UnitKeeperBot/handlers/add_task.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/add_task.py), [`UnitKeeperBot/templates/task_template.xlsx`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/templates/task_template.xlsx) | Miniapp + backend |
| Task list for management | Shows all active tasks in current group and opens detail card | `/list_of_tasks` | [`UnitKeeperBot/handlers/tasks.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/tasks.py) | Miniapp + backend |
| Task detail | Shows task ID, title, frequency, cost, remaining executions in sprint | task detail callback | [`UnitKeeperBot/handlers/tasks.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/tasks.py) | Miniapp + backend |
| Quick frequency adjustment | Task detail allows `+1` or `-1` frequency updates directly | detail callbacks | [`UnitKeeperBot/handlers/tasks.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/tasks.py) | Miniapp + backend |
| Task edit | Edit task by ID: title, frequency, cost | `/edit_task` | [`UnitKeeperBot/handlers/edit_task.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/edit_task.py) | Miniapp + backend |
| Task delete | Soft-delete task by ID after inline confirmation | `/delete_task` | [`UnitKeeperBot/handlers/delete_task.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/delete_task.py) | Miniapp + backend |
| Active task execution list | Shows only active tasks that still have remaining executions in current period | `/tasks` | [`UnitKeeperBot/handlers/tasks.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/tasks.py) | Miniapp + backend |
| Task completion flow | User marks task done; if group has one member, completion is auto-approved; otherwise creates `pending` log and asks other members to confirm | `/tasks` callbacks | [`UnitKeeperBot/handlers/tasks.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/tasks.py) | Miniapp + backend, bot for approval notifications |
| Task approval | Group members confirm a pending completion; system enforces sprint frequency cap and converts log to `completed` | confirm callback | [`UnitKeeperBot/handlers/tasks.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/tasks.py) | Bot + backend, miniapp inbox later |
| Task rejection | Group member rejects a pending completion with a free-text reason; performer gets notified | reject callback | [`UnitKeeperBot/handlers/tasks.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/tasks.py) | Bot + backend, miniapp inbox later |
| Sprint progress | Shows elapsed days, actual units, planned units by user weight, completed tasks, and progress bar | `/temp_results` | [`UnitKeeperBot/handlers/temp_results.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/temp_results.py) | Miniapp + backend |
| Sprint closing job | Daily scheduler runs near 23:59, checks whether today is sprint end for each group, calculates plan/fact, bonus, balances, and sends reports | background scheduler | [`UnitKeeperBot/sprint_results.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/sprint_results.py) | Backend + bot |
| Balance viewing | Shows current personal balance | `/balance` -> `Посмотреть баланс` | [`UnitKeeperBot/handlers/balance.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/balance.py) | Miniapp + backend |
| Unit transfer | Lets a user choose a group member and transfer units if balance is sufficient | `/balance` -> `Перевести юниты` | [`UnitKeeperBot/handlers/balance.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/balance.py) | Miniapp + backend |
| Kill remaining tasks | Admin-like destructive helper clears all remaining required executions in current week by lowering task frequencies | `/kill_tasks` | [`UnitKeeperBot/handlers/tasks.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/tasks.py) | Backend admin tool, not default miniapp UX |
| Help text | Manual help and command guide | `/help` | [`UnitKeeperBot/handlers/help.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/help.py) | Bot + docs |
| Product explanation | Explains the unit system and intended usage | `/about` | [`UnitKeeperBot/handlers/about.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers/about.py) | Miniapp content + bot fallback |

## User Flows To Preserve

### Onboarding and membership
- New user can start without prior DB record.
- User without group is offered exactly two next actions: create a group or join a group.
- A user cannot create or join a new group without leaving the current one first.

### Group mechanics
- Group name must be unique.
- Group password is required for joining.
- Sprint has configurable start weekday and duration.
- Member workload is stored as percentages summing to 100.
- Ownership matters for settings management and owner handover on exit.

### Task mechanics
- Each task belongs to one group.
- Each task has a repeat count within a sprint and a unit cost per completion.
- A task can be active or soft-deleted.
- Remaining executions depend on completed logs within the current sprint window.

### Approval mechanics
- Single-member group skips approval and closes the task instantly.
- Multi-member group uses a pending confirmation flow.
- Confirmation must stop once frequency limit is reached.
- Rejection carries a free-text reason back to the performer.

### Economics
- Every member has a persistent personal balance.
- Group also has a collective balance concept.
- Members can transfer units to each other inside the same group.
- Sprint close recalculates plan/fact and mutates balances.

## Scheduler Behavior To Preserve
- There is a periodic job that checks all groups daily.
- Sprint end is computed from `start_day` and `sprint_duration`.
- At sprint close the system computes planned units for each user from total task cost volume and user weight.
- At sprint close the system computes actual units from completed logs in the sprint window.
- At sprint close the system computes efficiency.
- At sprint close the system adjusts balances.
- At sprint close the system sends personal results to members.
- At sprint close the system sends a group summary to the owner.

## Important Legacy Mismatches
- README mentions invite codes for joining; actual code joins by group name plus password.
- README mentions CSV import/export; actual code imports from Excel template and does not implement export.
- README mentions a group benefit shop and Google Calendar; these are not implemented.
- `Group.group_balance` exists in the model, but sprint result code writes to `group.balance`, which is inconsistent and should not be ported blindly.
- Telegram names are fetched live from Telegram API, not stored in the database.
- Some handler state names and callback payloads are inconsistent; preserve user-facing intent, not these defects.

## Migration Notes
- First-class future surfaces are miniapp, backend, bot, and `common`.
- Miniapp is the primary product UX.
- Backend owns all business rules and scheduling.
- Bot owns notifications, approval prompts, reminders, and deep links into the miniapp.
- `common` owns DB schema, migrations, and shared persistence layer.
- During migration, every new feature spec should link back to the relevant rows in this document and the legacy files above.
