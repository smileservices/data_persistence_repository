import os
import pytest
from sqlalchemy import orm, create_engine, exc, text
from sqlalchemy_utils import create_database, drop_database, database_exists

from sql_repository import SqlRepository

from tests import fake

"""we test the actual implemetation of the data repository"""

# sqlite fails to raise IntegrityError
# test_db_url = "sqlite:///:memory:"
test_db_url = os.environ.get("POSTGRES_URL")
db_engine = create_engine(test_db_url)


@pytest.fixture()
def test_repo():
    if database_exists(test_db_url):
        drop_database(test_db_url)
    create_database(test_db_url)

    # Create an engine for the in-memory database
    repo = SqlRepository(engine=db_engine)
    repo.sync_schema()
    fake.run_mappers(repo.registry)

    yield repo

    # Cleanup code after tests complete
    orm.clear_mappers()
    db_engine.dispose()


def test_can_add(test_repo):
    test_model_instance = fake.TestModel(
        name='test item'
    )
    with test_repo.start_session() as s:
        test_repo.add(s, test_model_instance)

    with orm.Session(db_engine) as s:
        q = s.execute(text("SELECT * FROM test_table")).all()
    assert len(q) == 1
    assert q[0][0] == 1
    assert q[0][1] == 'test item'


def test_can_map_relationship(test_repo):
    test_model_instance = fake.TestModel(
        name='test item',
        joined=[fake.TestJoinedModel(), fake.TestJoinedModel()]
    )
    with test_repo.start_session() as s:
        test_repo.add(s, test_model_instance)
    # test that child row is added to the joined table
    with orm.Session(db_engine) as s:
        q = s.execute(text("SELECT * FROM test_joined_table")).all()
    assert len(q) == 2
    assert q[0][0] == 1
    assert q[0][1] == 1
    # test the orm relationship mapping
    with test_repo.start_session() as s:
        joined = s.query(fake.TestJoinedModel).all()
        assert len(joined) == 2
        assert [j.parent_id for j in joined] == [1, 1]
        parent = s.query(fake.TestModel).one()
        assert parent.joined == joined


def test_can_add_bulk(test_repo):
    test_model_instances = [
        fake.TestModel(name='test item 1'),
        fake.TestModel(name='test item 2'),
        fake.TestModel(name='test item 3')
    ]
    with test_repo.start_session() as s:
        test_repo.add_bulk(s, test_model_instances)
    # test that child row is added to the joined table
    with orm.Session(db_engine) as s:
        q = s.execute(text("SELECT * FROM test_table")).all()
    assert len(q) == 3
    assert [i.name for i in q] == ['test item 1', 'test item 2', 'test item 3']


def test_can_get(test_repo):
    with orm.Session(db_engine) as s:
        q = s.execute(text(
            "INSERT INTO test_table(name) VALUES ('t1'), ('t2')"
        ))
        s.commit()
    with test_repo.start_session() as s:
        result = test_repo.get(s, fake.TestModel, name='t2')
        assert result.id == 2
        assert result.name == 't2'


def test_can_delete(test_repo):
    with orm.Session(db_engine) as s:
        q = s.execute(
            text("INSERT INTO test_table(name) VALUES ('t1'), ('t2')")
        )
        s.commit()
    with test_repo.start_session() as s:
        test_repo.delete(s, fake.TestModel, name='t1')
    with orm.Session(db_engine) as s:
        q = s.execute(text("SELECT * FROM test_table")).all()
    assert len(q) == 1
    assert q[0][1] == 't2'


def test_can_filter(test_repo):
    with orm.Session(db_engine) as s:
        q = s.execute(
            text("INSERT INTO test_table(name) VALUES ('t1'), ('t2'), ('t3')")
        )
        s.commit()
    with test_repo.start_session() as s:
        result = test_repo.filter(s, fake.TestModel, fake.TestModel.id > 1)
        assert len(result) == 2
        assert [i.name for i in result] == ['t2', 't3']


def test_can_rollback(test_repo):
    with orm.Session(db_engine) as s:
        s.execute(text("INSERT INTO test_table(name) VALUES ('t1')"))
        s.commit()
        s.execute(text("INSERT INTO test_joined_table(parent_id) VALUES (1)"))
        s.commit()
    with pytest.raises(exc.IntegrityError) as e:
        with test_repo.start_session() as s:
            result = test_repo.filter(s, fake.TestJoinedModel, fake.TestJoinedModel.parent_id == 1)
            assert type(result[0]) == fake.TestJoinedModel
            result[0].parent_id = 2
    with orm.Session(db_engine) as s:
        q = s.execute(text("SELECT * FROM test_joined_table")).all()
        assert q[0][1] == 1


def test_exists(test_repo):
    with orm.Session(db_engine) as s:
        q = s.execute(
            text("INSERT INTO test_table(name) VALUES ('t1'), ('t2'), ('t3')")
        )
        s.commit()
    with test_repo.start_session() as s:
        assert test_repo.exists(s, fake.TestModel, name='t1')
    with test_repo.start_session() as s:
        assert not test_repo.exists(s, fake.TestModel, name='t100')


def test_patch(test_repo):
    with orm.Session(db_engine) as s:
        q = s.execute(
            text("INSERT INTO test_table(id, name) VALUES (1, 't1'), (2, 't2'), (3, 't3')")
        )
        s.commit()

    # Patch the 'name' attribute for the records where 'id' is greater than 1
    with test_repo.start_session() as s:
        test_repo.patch(s, fake.TestModel, update_data={'name': 'updated'}, id=1)

    # Validate the update operation
    with orm.Session(db_engine) as s:
        result = test_repo.get(s, fake.TestModel, id=1)
        result_not = test_repo.get(s, fake.TestModel, id=2)
    assert result.name == 'updated'
    assert result_not.name == 't2'
