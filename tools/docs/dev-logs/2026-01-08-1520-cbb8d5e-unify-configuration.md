# Step 1: Unify Configuration (COMPLETED)

- Removed legacy `settings.py`
- All code uses `config/app_config.py` (Pydantic-based)
- Configuration accessed via `AppContext.config`