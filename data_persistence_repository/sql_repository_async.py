from typing import List, Iterable, Optional
import contextlib
import asyncio

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
)
from sqlalchemy import MetaData, select, delete, update
from sqlalchemy.orm import registry
from sqlalchemy.exc import NoResultFound

from .repository_interface import Repository

import logging

logger = logging.getLogger("sql_repository")


class AsyncSqlRepository(Repository):
    metadata_obj = MetaData()
    registry = registry()

    def __init__(self, url: Optional[str] = None, engine: Optional[AsyncEngine] = None):
        """
        Asynchronous SQL repository.
        :param url: SQL URL for the database connection.
        :param engine: Async engine, if already created.
        """
        if engine is None and url is None:
            raise ValueError("Either url or engine must be provided")

        self._engine = engine if engine else create_async_engine(url, echo=True, pool_recycle=3600, pool_pre_ping=True)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False, class_=AsyncSession)

    async def get_session(self):
        return self._session_factory()

    @contextlib.asynccontextmanager
    async def start_session(self, rollback=True):
        """
            use this context manager mainly
            retries in case of bad connection
        """
        async with self._session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback() if rollback else None
                raise
            else:
                try:
                    await session.commit()
                except Exception as ex:
                    logger.error(f"SQL Commit Error (FINAL): {str(ex)}")
                    await session.rollback() if rollback else None
                    raise

    async def sync_schema(self):
        """Asynchronously create tables and run migrations."""
        async with self._engine.begin() as conn:
            await conn.run_sync(self.metadata_obj.create_all)

    async def add(self, session: AsyncSession, instance: object):
        """Asynchronously save an object."""
        session.add(instance)

    async def add_bulk(self, session: AsyncSession, objects: List[object]):
        """Asynchronously save a list of objects."""
        session.add_all(objects)

    async def get(self, session: AsyncSession, model, **kwargs):
        """Asynchronously get an object."""
        try:
            result = await session.execute(select(model).filter_by(**kwargs))
            return result.scalar_one()
        except NoResultFound:
            return None

    async def exists(self, session: AsyncSession, model, **kwargs) -> bool:
        """Asynchronously check if an object exists."""
        result = await session.execute(select(model).filter_by(**kwargs))
        return result.scalar_one_or_none() is not None

    async def delete(self, session: AsyncSession, model, **kwargs):
        """Asynchronously delete an object."""
        await session.execute(delete(model).filter_by(**kwargs))

    async def filter(self, session: AsyncSession, model, *args, **kwargs) -> Iterable:
        """Asynchronously get a list of objects after applying some filtering."""
        if args and kwargs:
            raise ValueError('Cannot use filter method with both args and kwargs')

        if args:
            result = await session.execute(select(model).filter(*args))
        elif kwargs:
            result = await session.execute(select(model).filter_by(**kwargs))
        else:
            result = await session.execute(select(model))

        # because we're usually using lazy="joined"
        return result.unique().scalars().all()

    async def filter_by_list(self, session: AsyncSession, model, field: str, items_list: List) -> Iterable:
        """Asynchronously filter objects by a list of values in a field."""
        query_field = getattr(model, field)
        result = await session.execute(select(model).filter(query_field.in_(items_list)))
        return result.scalars().all()

    async def patch(self, session: AsyncSession, model, update_data: dict, **kwargs):
        """Asynchronously update specific fields of an object."""
        await session.execute(update(model).filter_by(**kwargs).values(update_data))
