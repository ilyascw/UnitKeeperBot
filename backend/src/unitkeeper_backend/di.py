from __future__ import annotations

from collections.abc import AsyncIterable

from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from unitkeeper_backend.application.auth.service import AuthService
from unitkeeper_backend.application.bot.service import BotService
from unitkeeper_backend.application.context.service import CurrentContextService
from unitkeeper_backend.application.groups.service import GroupService
from unitkeeper_backend.application.sprints.service import SprintService
from unitkeeper_backend.application.tasks.service import TaskService
from unitkeeper_backend.config import Settings, settings
from unitkeeper_backend.infrastructure.auth.session_tokens import HmacSessionTokenManager
from unitkeeper_backend.infrastructure.auth.telegram import TelegramWebAppVerifier
from unitkeeper_backend.infrastructure.db.session import build_engine, build_session_maker
from unitkeeper_backend.infrastructure.time import UtcClock
from unitkeeper_backend.infrastructure.uow.sqlalchemy import SqlAlchemyUnitOfWork


class AppProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_settings(self) -> Settings:
        return settings

    @provide(scope=Scope.APP)
    def provide_engine(self, settings: Settings) -> AsyncEngine:
        return build_engine(settings)

    @provide(scope=Scope.APP)
    def provide_session_maker(
        self,
        engine: AsyncEngine,
    ) -> async_sessionmaker[AsyncSession]:
        return build_session_maker(engine)

    @provide(scope=Scope.APP)
    def provide_clock(self) -> UtcClock:
        return UtcClock()

    @provide(scope=Scope.APP)
    def provide_telegram_verifier(self, settings: Settings) -> TelegramWebAppVerifier:
        return TelegramWebAppVerifier(
            bot_token=settings.telegram_bot_token,
            max_age_seconds=settings.telegram_auth_max_age_seconds,
        )

    @provide(scope=Scope.APP)
    def provide_session_manager(self, settings: Settings) -> HmacSessionTokenManager:
        return HmacSessionTokenManager(
            secret=settings.session_secret,
            ttl_seconds=settings.session_ttl_seconds,
        )

    @provide(scope=Scope.REQUEST)
    async def provide_session(
        self,
        session_maker: async_sessionmaker[AsyncSession],
    ) -> AsyncIterable[AsyncSession]:
        async with session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

    @provide(scope=Scope.REQUEST)
    def provide_uow(self, session: AsyncSession) -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session)

    @provide(scope=Scope.REQUEST)
    def provide_context_service(self, uow: SqlAlchemyUnitOfWork) -> CurrentContextService:
        return CurrentContextService(uow=uow)

    @provide(scope=Scope.REQUEST)
    def provide_auth_service(
        self,
        uow: SqlAlchemyUnitOfWork,
        verifier: TelegramWebAppVerifier,
        token_manager: HmacSessionTokenManager,
        clock: UtcClock,
        context_service: CurrentContextService,
    ) -> AuthService:
        return AuthService(
            uow=uow,
            verifier=verifier,
            token_manager=token_manager,
            clock=clock,
            context_service=context_service,
        )

    @provide(scope=Scope.REQUEST)
    def provide_group_service(
        self,
        uow: SqlAlchemyUnitOfWork,
        context_service: CurrentContextService,
        clock: UtcClock,
    ) -> GroupService:
        return GroupService(uow=uow, context_service=context_service, clock=clock)

    @provide(scope=Scope.REQUEST)
    def provide_task_service(self, uow: SqlAlchemyUnitOfWork, clock: UtcClock) -> TaskService:
        return TaskService(uow=uow, clock=clock)

    @provide(scope=Scope.REQUEST)
    def provide_sprint_service(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: UtcClock,
    ) -> SprintService:
        return SprintService(uow=uow, clock=clock)

    @provide(scope=Scope.REQUEST)
    def provide_bot_service(
        self,
        uow: SqlAlchemyUnitOfWork,
        context_service: CurrentContextService,
        task_service: TaskService,
    ) -> BotService:
        return BotService(
            uow=uow,
            context_service=context_service,
            task_service=task_service,
        )


def setup_di(app) -> None:
    container = make_async_container(AppProvider())
    setup_dishka(container=container, app=app)
    app.state.dishka_container = container
