from __future__ import annotations
from dataclasses import dataclass, field
from sqlalchemy import Table, Column, Integer, String, ForeignKey, orm
from sql_repository import SqlRepository
from typing import List, Optional


# Imperative style
metadata = SqlRepository.metadata_obj

test_table = Table(
    'test_table',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(50))
)

test_joined_table = Table(
    'test_joined_table',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('parent_id', Integer, ForeignKey('test_table.id'))
)


@dataclass
class TestModel:
    id: int = field(init=False)
    name: str = None
    joined: Optional[List[TestJoinedModel]] = field(default_factory=list)


@dataclass
class TestJoinedModel:
    id: int = field(init=False)
    parent_id: int = field(init=False)


def run_mappers(registry):
    registry.map_imperatively(TestModel, test_table, properties={
        "joined": orm.relationship(TestJoinedModel, backref='parent')
    })
    registry.map_imperatively(TestJoinedModel, test_joined_table)
