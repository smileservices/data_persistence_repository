import os
import pytest
import logging

from sqlalchemy import orm, create_engine, exc, text, select
from sqlalchemy_utils import create_database, drop_database, database_exists
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sql_repository_async import AsyncSqlRepository
from sql_repository import SqlRepository

from tests import fake

"""we test the actual implemetation of the data repository"""

# sqlite fails to raise IntegrityError
# test_db_url = "sqlite:///:memory:"
test_db_url = os.environ.get("ASYNC_POSTGRES_URL")

# to use with sqlalchemy_utils
sync_test_db_url = os.environ.get("POSTGRES_URL")

db_engine = create_engine(sync_test_db_url)
async_db_engine = create_async_engine(test_db_url)
async_sess_factory = async_sessionmaker(async_db_engine, class_=AsyncSession)

logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)


@pytest.fixture()
async def test_repo():
    if database_exists(sync_test_db_url):
        drop_database(sync_test_db_url)
    create_database(sync_test_db_url)

    sync_repo = SqlRepository(url=sync_test_db_url)
    sync_repo.sync_schema()
    fake.run_mappers(sync_repo.registry)

    # Create an engine for the in-memory database
    async_repo = AsyncSqlRepository(engine=async_db_engine)


    yield async_repo

    # Cleanup code after tests complete
    orm.clear_mappers()
    await async_db_engine.dispose()


@pytest.mark.asyncio
async def test_can_add(test_repo):
    test_model_instance = fake.TestModel(
        name='test item'
    )
    async with test_repo.start_session() as s:
        await test_repo.add(s, test_model_instance)

    async with async_sess_factory() as s:
        q = await s.execute(text("SELECT * FROM test_table"))
        res = q.all()
    assert len(res) == 1
    assert res[0][0] == 1
    assert res[0][1] == 'test item'


@pytest.mark.asyncio
async def test_can_map_relationship(test_repo):
    test_model_instance = fake.TestModel(
        name='test item',
        joined=[fake.TestJoinedModel(), fake.TestJoinedModel()]
    )
    async with test_repo.start_session() as s:
        await test_repo.add(s, test_model_instance)

    # test that child row is added to the joined table
    async with async_sess_factory() as s:
        res = await s.execute(text("SELECT * FROM test_joined_table"))
        q = res.all()
    assert len(q) == 2
    assert q[0][0] == 1
    assert q[0][1] == 1

    # test the orm relationship mapping
    async with test_repo.start_session() as s:
        q = await s.execute(select(fake.TestJoinedModel))
        joined = q.scalars().all()
        assert len(joined) == 2
        assert [j.parent_id for j in joined] == [1, 1]
        result = await s.execute(select(fake.TestModel))
        parent = result.scalars().one()
        # issues with lazyloading; to work
        assert parent.joined == joined


async def test_can_add_bulk(test_repo):
    test_model_instances = [
        fake.TestModel(name='test item 1'),
        fake.TestModel(name='test item 2'),
        fake.TestModel(name='test item 3')
    ]
    async with test_repo.start_session() as s:
        await test_repo.add_bulk(s, test_model_instances)
    # test that child row is added to the joined table
    async with test_repo.start_session() as s:
        res = await s.execute(select(fake.TestModel))
        q = res.scalars().all()
        assert len(q) == 3
        assert [i.name for i in q] == ['test item 1', 'test item 2', 'test item 3']


async def test_can_get(test_repo: AsyncSqlRepository):
    async with async_sess_factory() as s:
        await s.execute(text(
            "INSERT INTO test_table(name) VALUES ('t1'), ('t2')"
        ))
        await s.commit()
    async with test_repo.start_session() as s:
        result = await test_repo.get(s, fake.TestModel, name='t2')
        assert result.id == 2
        assert result.name == 't2'


async def test_can_delete(test_repo: AsyncSqlRepository):
    async with async_sess_factory() as s:
        q = await s.execute(
            text("INSERT INTO test_table(name) VALUES ('t1'), ('t2')")
        )
        await s.commit()
    async with test_repo.start_session() as s:
        await test_repo.delete(s, fake.TestModel, name='t1')
    async with async_sess_factory() as s:
        res = await s.execute(select(fake.TestModel))
        q = res.scalars().all()
    assert len(q) == 1
    assert q[0].name == 't2'


async def test_can_filter(test_repo: AsyncSqlRepository):
    async with async_sess_factory() as s:
        q = await s.execute(
            text("INSERT INTO test_table(name) VALUES ('t1'), ('t2'), ('t3')")
        )
        await s.commit()
    async with test_repo.start_session() as s:
        result = await test_repo.filter(s, fake.TestModel, fake.TestModel.id > 1)
        assert len(result) == 2
        assert [i.name for i in result] == ['t2', 't3']


async def test_can_rollback(test_repo):
    async with async_sess_factory() as s:
        await s.execute(text("INSERT INTO test_table(name) VALUES ('t1')"))
        await s.commit()
        await s.execute(text("INSERT INTO test_joined_table(parent_id) VALUES (1)"))
        await s.commit()
    with pytest.raises(exc.IntegrityError) as e:
        async with test_repo.start_session() as s:
            result = await test_repo.filter(s, fake.TestJoinedModel, fake.TestJoinedModel.parent_id == 1)
            assert type(result[0]) == fake.TestJoinedModel
            result[0].parent_id = 2
    async with async_sess_factory() as s:
        q = await s.execute(select(fake.TestModel))
        res = q.scalars().all()
        assert res[0].id == 1


async def test_exists(test_repo):
    async with async_sess_factory() as s:
        q = await s.execute(
            text("INSERT INTO test_table(name) VALUES ('t1'), ('t2'), ('t3')")
        )
        await s.commit()
    async with test_repo.start_session() as s:
        assert await test_repo.exists(s, fake.TestModel, name='t1')
    async with test_repo.start_session() as s:
        assert not await test_repo.exists(s, fake.TestModel, name='t100')


async def test_patch(test_repo):
    async with async_sess_factory() as s:
        await s.execute(
            text("INSERT INTO test_table(id, name) VALUES (1, 't1'), (2, 't2'), (3, 't3')")
        )
        await s.commit()

    # Patch the 'name' attribute for the records where 'id' is greater than 1
    async with test_repo.start_session() as s:
        await test_repo.patch(s, fake.TestModel, update_data={'name': 'updated'}, id=1)

    # Validate the update operation
    async with test_repo.start_session() as s:
        result = await test_repo.get(s, fake.TestModel, id=1)
        result_not = await test_repo.get(s, fake.TestModel, id=2)
    assert result.name == 'updated'
    assert result_not.name == 't2'
