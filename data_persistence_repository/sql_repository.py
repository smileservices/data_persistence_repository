from typing import List, Iterable, Optional
import contextlib

from sqlalchemy import create_engine, orm, MetaData, Engine
from sqlalchemy.exc import NoResultFound

from data_persistence_repository.repository_interface import Repository

'''
Read about how to map dataclasses to sqlalchemy tables here:
https://docs.sqlalchemy.org/en/14/orm/dataclasses.html#mapping-dataclasses-using-imperative-mapping
'''

import logging

logger = logging.getLogger("sql_repository")


class SqlRepository(Repository):
    metadata_obj = MetaData()
    registry = orm.registry()

    def __init__(
            self,
            url: Optional[str] = None,
            engine: Optional[Engine] = None
    ):
        """
        https://docs.sqlalchemy.org/en/14/core/pooling.html#pool-disconnects
        :param url: sql url
        :param engine: sql engine
        """
        # Pessimistic testing of connections that recycles connections to avoid stale
        self._engine = engine if engine else create_engine(url, pool_pre_ping=True, pool_recycle=3600)
        self.session = None

    @contextlib.contextmanager
    def start_session(self, rollback=True):
        """
            use this context manager mainly
            retries in case of bad connection
        """
        with self.get_session() as session:
            try:
                yield session
            except Exception as e:
                session.rollback() if rollback else None
                raise
            else:
                try:
                    session.commit()
                except Exception as ex:
                    logger.error(f"SQL Commit Error (FINAL): {str(ex)}")
                    session.rollback() if rollback else None
                    raise

    def get_session(self):
        return orm.Session(self._engine, expire_on_commit=False)

    def sync_schema(self):
        # create tables, run migrations, etc
        self.metadata_obj.create_all(self._engine)

    def add(self, session: orm.Session, instance: object):
        """save object"""
        return session.add(instance)

    def add_bulk(self, session: orm.Session, objects: List[object]):
        """save a list of objects"""
        session.add_all(objects)

    def get(self, session: orm.Session, model, **kwargs):
        """get object"""
        try:
            return session.query(model).filter_by(**kwargs).one()
        except NoResultFound:
            return None

    def exists(self, session: orm.Session, model, **kwargs) -> bool:
        res = self.get(session, model, **kwargs)
        return bool(res)

    def delete(self, session: orm.Session, model, **kwargs):
        """delete object"""
        session.query(model).filter_by(**kwargs).delete()

    def filter(self, session: orm.Session, model, *args, **kwargs) -> Iterable:
        """get a list of iterable objects after applying some filtering"""
        if args and kwargs:
            raise ValueError('Cannot use filter method with both args and kwargs')
        if args:
            res = session.query(model).filter(*args).all()
        elif kwargs:
            res = session.query(model).filter_by(**kwargs).all()
        return res

    def filter_by_list(self, session: orm.Session, model, field: str, items_list: List) -> Iterable:
        query_field = getattr(model, field)
        return session.query(model).filter(query_field.in_(items_list)).all()

    def patch(self, session: orm.Session, model, update_data: dict, **kwargs):
        """Update specific fields of an object"""
        session.query(model).filter_by(**kwargs).update(update_data, synchronize_session='fetch')
