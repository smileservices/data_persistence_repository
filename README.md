# Data Persistence Repository

[![PyPI](https://img.shields.io/pypi/v/data_persistence_repository)](https://pypi.org/project/data-persistence-repository)
[![Build Status](https://github.com/smileservices/data_persistence_repository/actions/workflows/sql_postgres.yml/badge.svg)](https://github.com/smileservices/data_persistence_repository/actions)
[![Coverage Status](https://coveralls.io/repos/github/smileservices/data_persistence_repository/badge.svg?branch=main)](https://coveralls.io/github/smileservices/data_persistence_repository?branch=main)

**Data Persistence Repository** is a Python package providing a portable implementation of the repository pattern for a
data persistence layer. For the moment there is only SQL support but it is planned to introduce more database types.
This package facilitates interaction with SQL databases through an abstracted interface, ensuring clean and maintainable
database interaction in Python applications.

![Diagram](https://github.com/smileservices/data_persistence_repository/blob/main/diagram.png)

## Features

- Abstract repository interface for streamlined data layer interactions.
- Async and sync SQL repository implementation with SQLAlchemy.
- Context manager for robust database session management.
- Methods for CRUD operations (Create, Read, Update, Delete).
- Support for filtering and bulk operations.

## Installation

Install **Data Persistence Repository** from PyPI:

```bash
pip install data_persistence_repository
```

## Usage

Basic usage example (synchron):

```python
from sqlalchemy.orm import Session
from data_persistence_repository.sql_repository import SqlRepository

class YourOwnRepository(SqlRepository):
    
    def special_query(self, session: Session):
        # execute a special query
        
# Initialize the repository
repo = YourOwnRepository("sqlite:///your_database.db")

# Use the repository within a managed context
with repo.start_session() as session:
    # Perform add, get, delete operations here
    repo.special_query(session)
```

Basic usage example (asynchron):

```python
from sqlalchemy.ext.asyncio import AsyncSession
from data_persistence_repository.sql_repository_async import AsyncSqlRepository

class YourOwnRepository(AsyncSqlRepository):
    
    async def special_query(self, session: AsyncSession):
        # execute a special query
        await session.execute(...)

# Initialize the repository
repo = AsyncSqlRepository("sqlite:///your_database.db")

# Use the repository within a managed context
async with repo.start_session() as session:
    # Perform add, get, delete operations here
    await repo.special_query(session)
```

Replace `"sqlite:///your_database.db"` with your actual database URL.

## Requirements

- Python 3.x
- Dependencies listed in `requirements.txt`.

## Running Tests

Execute tests using pytest:

```bash
python -m pytest tests
```

## Contributing

Contributions are welcomed! For substantial changes, please open an issue first to discuss what you'd like to change.
Please make sure to update tests accordingly. Also, each PR must have tests.

## License

[MIT](https://choosealicense.com/licenses/mit/)

---

For more information on the repository pattern and its benefits in data persistence, please
visit [Repository Design Pattern Information](https://www.geeksforgeeks.org/repository-design-pattern/).
