# UnitKeeper Architecture

This document captures two states of the project:

- legacy architecture from `UnitKeeperBot`;
- current migrated architecture in this repository.

## Legacy Bot Architecture

```mermaid
flowchart TB
    tg[Telegram users] --> polling[aiogram polling]
    polling --> bot[UnitKeeperBot/bot.py<br/>Bot + Dispatcher]

    bot --> routers[handlers/__init__.py<br/>router registry]
    bot --> schedulerSetup[sprint_results.setup_sprint_scheduler]

    subgraph handlers[Legacy handler modules]
        start[start.py<br/>/start bootstrap]
        help[help.py<br/>/help]
        about[about.py<br/>/about]
        group[group.py<br/>create group FSM]
        join[join_group.py<br/>join group FSM]
        exit[exit_group.py<br/>leave group + owner handover]
        groupInfo[group_info.py<br/>group info]
        settings[group_settings.py<br/>group settings + weights FSM]
        addTask[add_task.py<br/>single task + XLSX import]
        editTask[edit_task.py<br/>edit task FSM]
        deleteTask[delete_task.py<br/>soft delete task]
        tasks[tasks.py<br/>task list, done, approve, reject,<br/>frequency adjust, kill_tasks]
        balance[balance.py<br/>view balance + transfer units]
        temp[temp_results.py<br/>current sprint progress]
    end

    routers --> start
    routers --> help
    routers --> about
    routers --> group
    routers --> join
    routers --> exit
    routers --> groupInfo
    routers --> settings
    routers --> addTask
    routers --> editTask
    routers --> deleteTask
    routers --> tasks
    routers --> balance
    routers --> temp

    subgraph calculations[Legacy calculation module]
        scheduler[sprint_results.scheduler<br/>daily loop near 23:59]
        calc[sprint_results.calculate_results<br/>plan/fact, bonus, balances,<br/>personal and owner reports]
        endDate[sprint_results.get_sprint_end_date]
    end

    schedulerSetup --> scheduler
    scheduler --> calc
    calc --> endDate

    subgraph db[Legacy DB layer]
        dbSession[db/database.py<br/>async SQLAlchemy session]
        models[db/models.py<br/>Group, User, Task, Log, Balance]
        postgres[(PostgreSQL)]
    end

    routers --> dbSession
    calc --> dbSession
    dbSession --> models
    models --> postgres

    addTask --> xlsx[templates/task_template.xlsx]
    routers --> telegramApi[Telegram Bot API<br/>messages, callbacks, get_chat]
    calc --> telegramApi

    config[config.py<br/>BOT_TOKEN, DATABASE_URL] --> bot
    config --> dbSession
```

## Current Migrated Architecture

```mermaid
flowchart TB
    user[Telegram users] --> miniapp[miniapp<br/>Telegram Mini App<br/>React + Vite + Telegram UI Kit]
    user --> futureBot[bot<br/>planned thin bot]

    subgraph miniappLayer[Mini App layer]
        screens[src/screens<br/>Home, onboarding, group,<br/>create/join/settings/weights]
        authClient[src/auth<br/>Telegram init data session]
        apiClient[src/api<br/>typed endpoints, queries, mutations]
        routes[src/routes<br/>client routes]
    end

    miniapp --> screens
    miniapp --> authClient
    miniapp --> routes
    screens --> apiClient
    authClient --> apiClient

    apiClient --> publicApi[backend FastAPI<br/>/api/v1 public API]
    futureBot --> internalApi[backend FastAPI<br/>/api/v1/internal/bot API]

    subgraph backendApi[Backend API routers]
        healthRouter[health.py<br/>GET /health]
        authRouter[auth.py<br/>POST /auth/telegram<br/>GET /auth/me]
        groupsRouter[groups.py<br/>current group, members,<br/>settings, weights, create/join/leave]
        tasksRouter[tasks.py<br/>tasks CRUD/import,<br/>done, approve, reject]
        sprintsRouter[sprints.py<br/>current results,<br/>manual sprint close]
        internalBotRouter[internal_bot.py<br/>ensure user, context,<br/>approve/reject for bot]
    end

    publicApi --> healthRouter
    publicApi --> authRouter
    publicApi --> groupsRouter
    publicApi --> tasksRouter
    publicApi --> sprintsRouter
    internalApi --> internalBotRouter

    subgraph application[Backend application services]
        authService[AuthService<br/>Telegram auth + sessions]
        contextService[CurrentContextService]
        groupService[GroupService<br/>group lifecycle, settings, weights]
        taskService[TaskService<br/>task management + approval flow]
        sprintService[SprintService<br/>progress + sprint close]
        botService[BotService<br/>thin bot use cases]
    end

    authRouter --> authService
    authRouter --> contextService
    groupsRouter --> groupService
    tasksRouter --> taskService
    sprintsRouter --> sprintService
    internalBotRouter --> botService

    botService --> contextService
    botService --> taskService

    subgraph domain[Backend domain services]
        sprintMath[sprint_math.py<br/>sprint window, weights,<br/>planned units, progress math]
        errors[errors.py<br/>DomainError taxonomy]
    end

    groupService --> sprintMath
    taskService --> sprintMath
    sprintService --> sprintMath
    authService --> errors
    groupService --> errors
    taskService --> errors
    sprintService --> errors

    subgraph infra[Backend infrastructure]
        di[di.py<br/>Dishka providers]
        uow[SQLAlchemyUnitOfWork]
        repos[repositories<br/>users, groups, tasks, sprints]
        authInfra[auth infrastructure<br/>Telegram verifier, session tokens]
        clock[time.py<br/>system clock]
    end

    authService --> uow
    contextService --> uow
    groupService --> uow
    taskService --> uow
    sprintService --> uow
    botService --> uow
    authService --> authInfra
    taskService --> clock
    sprintService --> clock
    uow --> repos
    di --> authService
    di --> groupService
    di --> taskService
    di --> sprintService
    di --> uow

    subgraph common[common shared persistence layer]
        commonModels[src/db/models.py<br/>SQLAlchemy models]
        commonEnums[src/db/enums.py<br/>shared enums]
        commonDatabase[src/db/database.py<br/>engine, async sessionmaker]
        migrations[alembic<br/>schema migrations]
    end

    repos --> commonModels
    repos --> commonEnums
    uow --> commonDatabase
    migrations --> database[(PostgreSQL)]
    commonDatabase --> database
    commonModels --> database

    subgraph notYetDone[Planned / incomplete migration areas]
        balances[balances + unit transfers API]
        jobs[scheduler jobs for sprint closing]
        outbox[notification outbox + idempotency]
        reminders[pending approval and sprint reminders]
        thinBotImpl[thin bot implementation]
    end

    publicApi -. future work .-> balances
    publicApi -. future work .-> jobs
    publicApi -. future work .-> outbox
    publicApi -. future work .-> reminders
    futureBot -. future work .-> thinBotImpl
```
