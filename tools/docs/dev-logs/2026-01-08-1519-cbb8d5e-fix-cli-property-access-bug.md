# Step 0.1: Fix CLI Property Access Bug

**Completed:** Fixed debug output property access

- Changed `ctx.obj.dbpath` to `ctx.obj.config.db_path` in `src/tools/cli.py:31`
- Fixes AttributeError from incomplete configuration refactoring
- Verified with `tools --debug` - no errors, correct output