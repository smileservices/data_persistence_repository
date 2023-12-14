
# Data Persistence Repository SQL

[![PyPI](https://img.shields.io/pypi/v/data_persistence_repository)](https://pypi.org/project/data-persistence-repository-sql/)
[![Build Status](https://github.com/smileservices/data_persistence_repository/actions/workflows/sql_postgres.yml/badge.svg)](https://github.com/smileservices/data_persistence_repository/actions)
[![Coverage Status](https://coveralls.io/repos/github/smileservices/data_persistence_repository/badge.svg)](https://coveralls.io/github/smileservices/data_persistence_repository)

**Data Persistence Repository SQL** is a Python package providing a portable SQL repository implementation, following the repository pattern for a data persistence layer. This package facilitates interaction with SQL databases through an abstracted interface, ensuring clean and maintainable database interaction in Python applications.

## Features

- Abstract repository interface for streamlined data layer interactions.
- SQL repository implementation leveraging SQLAlchemy.
- Context manager for robust database session management.
- Comprehensive methods for CRUD operations (Create, Read, Update, Delete).
- Support for filtering and bulk operations.

## Installation

Install **Data Persistence Repository SQL** from PyPI:

```bash
pip install data_persistence_repository
```

## Usage

Basic usage example:

```python
from data_persistence_repository.sql_repository import SqlRepository

# Initialize the repository
repo = SqlRepository("sqlite:///your_database.db")

# Use the repository within a managed context
with repo.start_session() as session:
    # Perform add, get, delete operations here
```

Replace `"sqlite:///your_database.db"` with your actual database URL.

## Requirements

- Python 3.x
- Dependencies listed in `requirements.txt`.

## Running Tests

Execute tests using pytest:

```bash
pytest
```

## Contributing

Contributions are welcomed! For substantial changes, please open an issue first to discuss what you'd like to change. Please make sure to update tests accordingly.

## License

[MIT](https://choosealicense.com/licenses/mit/)

---

For more information on the repository pattern and its benefits in data persistence, please visit [Repository Pattern Information](https://example.com/repository-pattern-info).
