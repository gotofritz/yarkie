# Yarkie Tools

When you need to refer to the current plan or architecture, refer to [`claude/project-plan.md`](claude/project-plan.md).

## Code Conventions

### Python

- Ruff formatting (line length 88, double quotes, 4-space indentation)
- Type hints throughout (modern Python 3.13+ syntax like `str | None`)
- Pydantic models
- Prefer async if possible

### Development tasks

- Task is set up to l

### Architecture Patterns

- Click for CLI with command groups and dependency injection via `@click.pass_context`
- Repository pattern for data access with explicit dependency injection
- Service layer for business logic (`ArchiverService`)
- SQLAlchemy Core (not ORM) with explicit sessions

### Data storage

- sqlite is used to store data
- alembic is used to manage migrations
- the local file system is used to store files, the location is in app_config.DEFAULT_DATA_ROOT

### File Organization

- `__init__.py` files are mostly empty (11 instances)
- `main.py` for command group collectors
- Clear module separation: `data_access/`, `models/`, `services/`, `helpers/`
- Configuration in `config/app_config.py` using Pydantic Settings

### Error Handling

- Custom exceptions in `exceptions.py` (currently minimal, to be preferred)
- Avoid `except Exception` unless unavoidable
- Logging with structured messages

### Testing

- 95% coverage requirement
- Pytest function-based tests with async support
- Faker, polyfactory and pytest-data for test data generation

### Commands

- Dev tas

## Important file locations

- The main python package is in tools/
- Config lives in tools/config/
- migrations are in alembic/versions/
- scripts/ contains generic one off files, which can normally be ignored
