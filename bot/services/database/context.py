import asyncio
from types import TracebackType
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .repositories import Repository
from .uow import UoW


class SQLSessionContext:
    """
    The context manager for the database session.
    """

    _session_pool: async_sessionmaker[AsyncSession]
    _session: Optional[AsyncSession]

    def __init__(self, session_pool: async_sessionmaker[AsyncSession]) -> None:
        """
        Initialize the context manager.

        :param session_pool: The session pool.
        """
        self._session_pool = session_pool
        self._session = None

    async def __aenter__(self) -> tuple[Repository, UoW]:
        """
        Enter the context manager.

        :return: The repository and unit of work.
        """
        self._session: AsyncSession = await self._session_pool().__aenter__()
        return Repository(session=self._session), UoW(session=self._session)

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """
        Exit the context manager.

        :param exc_type: The exception type.
        :param exc_value: The exception value.
        :param traceback: The traceback.
        """
        if self._session is None:
            return
        task: asyncio.Task[None] = asyncio.create_task(self._session.close())
        await asyncio.shield(task)
        self._session = None
