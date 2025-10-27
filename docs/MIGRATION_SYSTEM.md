# Migration System Documentation

## UPDATE: System 2 is Now Active (2025-10-27)

**User decision**: External migration files are the correct pattern. Inline migrations in `core/migrations.py` are "pants on head stupid" (user's words).

### System 1: Legacy Inline System (`core/migrations.py`)
- **Location**: `server/core/migrations.py`
- **Pattern**: Inline functions with `Migration(version, name, func)` registration
- **Auto-runs**: Yes, on `ComplianceDatabase.__init__()`
- **Tracking**: `schema_migrations` table
- **Status**: ⚠️ LEGACY - DO NOT ADD NEW MIGRATIONS HERE
- **Applied Migrations**:
  - v1-7: Various column additions (base_url, screenshot_path, deleted_at, token tracking, etc.)
  - v8: add_versioning_and_logging (adds digest versioning, INCOMPLETE for rules)

### System 2: External Migration Files (`server/migrations/`)
- **Location**: `server/migrations/*.py` files
- **Pattern**: Separate files with `upgrade(conn)` and `downgrade(conn)` functions
- **Auto-runs**: ❌ NO - Must be run manually
- **Docker Mount**: ✅ NOW MOUNTED (added to docker-compose.yml line 22)
- **Tracking**: Run manually, not auto-tracked
- **Status**: ✅ ACTIVE - USE THIS FOR NEW MIGRATIONS
- **Files**:
  - 006-007: Duplicates of System 1 migrations (historical)
  - 008-010: Page types system
  - 011: Preamble system
  - 012-013: Rules system (migration 13 creates core tables)
  - 014: Versioning and logging (failed - digest columns already existed)
  - **015**: ✅ Complete rules lineage (successfully applied 2025-10-27)

## How Migration 13 Got Applied

Migration 13 from System 2 was applied (shows in schema_migrations table as version 13), but:
1. The `/server/migrations/` directory is NOT mounted in Docker
2. There's no runner in the codebase that loads these files
3. Must have been run manually via direct SQL execution or temporary script

## Current Database State (Updated 2025-10-27)

### ✅ Tables and Columns (Complete)
- `states` - Core state definitions
- `legislation_sources` - Uploaded legislation files
- `legislation_digests` - WITH version and active columns (for versioning)
- `rules` - WITH all lineage columns:
  - ✅ legislation_digest_id
  - ✅ is_manually_modified
  - ✅ original_rule_text
  - ✅ status
  - ✅ supersedes_rule_id
- `page_types` - 18 dealership page types
- `rule_collisions` - ✅ Created by migration 015
- `llm_logs` - ✅ Created by migration 015
- All preamble system tables

### 📊 Schema is Now Complete
All planned schema changes from DESIGN_NOTES.md have been applied:
- ✅ Digest versioning (version, active)
- ✅ Rules lineage (5 columns)
- ✅ Collision detection table
- ✅ Comprehensive LLM logging

## How to Run Migrations Going Forward

### For New Migrations (Use System 2)

1. **Create migration file** in `server/migrations/`:
   ```bash
   # Example: 016_your_migration_name.py
   ```

2. **Use this template**:
   ```python
   import sqlite3
   import logging

   logger = logging.getLogger(__name__)

   def upgrade(conn: sqlite3.Connection):
       """Apply migration."""
       cursor = conn.cursor()
       # Your SQL here
       conn.commit()

   def downgrade(conn: sqlite3.Connection):
       """Rollback migration."""
       cursor = conn.cursor()
       # Rollback SQL here
       conn.commit()
   ```

3. **Run migration**:
   ```bash
   docker exec autoaudit-server sh -c "python /app/migrations/016_your_migration_name.py"
   ```

4. **Verify**:
   ```bash
   docker exec autoaudit-server python -c "
   import sqlite3
   conn = sqlite3.connect('/app/data/compliance.db')
   cursor = conn.cursor()
   cursor.execute('PRAGMA table_info(your_table)')
   print(cursor.fetchall())
   "
   ```

### System 1 Auto-Migrations (Legacy)

System 1 (`core/migrations.py`) still runs automatically on server startup for migrations 1-8. These are LEGACY and should not be modified. New migrations should use System 2.
- Auto-runs on startup
- Simple and working (except for v8)
- Well-documented in codebase

Action items:
1. Delete or comment out migration_008 from `core/migrations.py`
2. Add migration_009 to add missing columns/tables
3. Update MIGRATIONS list to skip to version 9
4. Document that v13 was applied externally
5. Archive `/server/migrations/` folder with a README explaining they're deprecated

## Migration Pattern Reference

### System 1 Pattern
```python
def migration_009_complete_rules_system(conn: sqlite3.Connection):
    """Add missing rules lineage and logging tables."""
    cursor = conn.cursor()

    # Add columns to rules
    try:
        cursor.execute("ALTER TABLE rules ADD COLUMN legislation_digest_id INTEGER")
    except sqlite3.OperationalError as e:
        if "duplicate column" not in str(e).lower():
            raise

    # Create new tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rule_collisions (...)
    """)

    conn.commit()

# Register it
MIGRATIONS = [
    # ... existing ...
    Migration(9, "complete_rules_system", migration_009_complete_rules_system),
]
```

### System 2 Pattern (Deprecated)
```python
def up(cursor):
    """Apply migration."""
    cursor.execute("CREATE TABLE ...")

def down(cursor):
    """Rollback migration."""
    cursor.execute("DROP TABLE ...")
```
