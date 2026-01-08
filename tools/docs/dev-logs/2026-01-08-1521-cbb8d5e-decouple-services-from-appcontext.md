# Step 2: Decouple Services from AppContext (COMPLETED)

**Completed:** Factory functions added to service files, AppContext refactored to accept injected dependencies, CLI and commands updated to use factories.

**What was done:**

1. **Added Factory Functions to Service Files**

   - `create_sql_client()` in `sql_client.py`
   - `create_local_db_repository()` in `local_db_repository.py`
   - `create_archiver_service()` in `archiver_service.py`
   - Factory functions collocated with their services for better cohesion

2. **Refactored AppContext to Accept Injected Dependencies**

   - Removed internal service creation
   - Constructor now requires `config`, `logger`, and `db` as parameters
   - Follows Single Responsibility Principle

3. **Updated CLI Entry Point** (`cli.py`)

   - Uses factory functions to create services
   - Passes fully-constructed dependencies to `AppContext`
   - Explicit dependency construction at entry point

4. **Updated Commands to Use Factory Functions**
   - `playlist/refresh.py` uses `create_archiver_service()`
   - `db/sync_local.py` uses `create_archiver_service()`
   - Removed manual service instantiation

**Testing:**

- ✅ Added tests for all factory functions (6 tests)
- ✅ Updated `mock_config` fixture to include `db_path`
- ✅ All existing tests pass (36 passed, 15 xfailed)
- ✅ QA checks pass (ruff, ty, coverage ≥ 20%)