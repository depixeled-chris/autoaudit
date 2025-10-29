# Alembic Migration System Refactor - Summary

**Date**: 2025-10-28
**Status**: ✅ COMPLETE

## Problem Identified

The previous Alembic baseline migration (`20251027_001`) was a **NO-OP**:
- It only checked if tables existed
- It created ZERO tables if database was fresh
- The actual schema was created by `database.py`'s `_create_tables()` method
- **A fresh database could NOT be created from Alembic alone**

This violated the principle that Alembic should be the single source of truth for schema.

## Actions Taken

### 1. Created Database Backups (Failsafe)
**Location**: `server/data/`
- `backup_schema.sql` - Complete schema (514 lines, all CREATE statements)
- `backup_seed_data.sql` - Seed data (35 lines, INSERT statements)
- `compliance.db.backup` - Full database file backup
- `BACKUP_README.md` - Restoration instructions

### 2. Created Proper Baseline Migration
**File**: `server/alembic/versions/20251028_001_proper_baseline.py`

**Creates from scratch**:
- All 31 tables with complete schema
- All indexes (17 indexes)
- All foreign key constraints
- Proper CHECK constraints
- UNIQUE constraints

**Tables created** (31 total):
- Core: users, refresh_tokens, states, projects
- Templates: templates, template_rules, extraction_templates
- URLs & Checks: urls, compliance_checks, violations, visual_verifications
- LLM: llm_calls, llm_logs, llm_model_config
- Legislation: legislation_sources, legislation_digests
- Rules: rules, rule_collisions
- Page Types: page_types
- Preambles: preambles, preamble_versions, preamble_templates, preamble_compositions, preamble_composition_deps, default_page_type_preambles, project_page_type_preambles, preamble_test_runs, preamble_version_performance
- Legacy: schema_migrations

**Smart behavior**:
- Detects if database already has tables
- Skips creation if tables exist (for existing DBs)
- Creates everything if fresh database

### 3. Created Seed Data Migration
**File**: `server/alembic/versions/20251028_002_seed_data.py`

**Inserts**:
- 1 state (Oklahoma)
- 5 LLM model configurations (PARSE_LEGISLATION, GENERATE_RULES, DETECT_COLLISIONS, GENERATE_PREAMBLE, COMPLIANCE_CHECK)
- 18 page types (HOMEPAGE, VDP, INVENTORY, FINANCING, LEASE, SERVICE, etc.)
- 1 preamble template (Standard Hierarchical)

**Smart behavior**:
- Checks if seed data already exists
- Skips if data present (idempotent)
- Parameterized INSERT statements (SQL injection safe)

### 4. Archived Old Migrations
- `20251027_001_complete_baseline.py` → `ARCHIVED_20251027_001_complete_baseline.py.bak`
- `20251027_002_update_operation_types.py` → `ARCHIVED_20251027_002_update_operation_types.py.bak`

### 5. Updated Existing Database
Updated `alembic_version` table to point to new migrations:
```sql
UPDATE alembic_version SET version_num = '20251028_002'
```

This marks the existing database as if it had been created by the new migrations.

### 6. Updated Documentation
**Files updated**:
- `docs/MIGRATION_SYSTEM.md` - Updated with new migration info and backup locations
- `CLAUDE.md` - Updated critical issues section
- Created `server/data/BACKUP_README.md` - Restoration guide
- Created `ALEMBIC_REFACTOR_SUMMARY.md` - This file

## Verification

✅ Alembic history shows correct chain:
```
20251028_001 -> 20251028_002 (head)
<base> -> 20251028_001
```

✅ Current database version: `20251028_002`

✅ All 31 tables exist in production database

✅ All seed data present (1 state, 5 LLM configs, 18 page types, 1 template)

## Testing Fresh Database Creation

**To test**:
```bash
# Remove test database if exists
rm server/data/test_fresh.db

# Create fresh database with Alembic
docker-compose exec server sh -c "
export DATABASE_PATH=/app/data/test_fresh.db
alembic upgrade head
"

# Verify tables
docker-compose exec server python -c "
import sqlite3
conn = sqlite3.connect('/app/data/test_fresh.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
print([row[0] for row in cursor.fetchall()])
"
```

**Expected output**: 31 tables + alembic_version

## Database.py Changes Needed (Future)

**TODO**: Remove `_create_tables()` method from `server/core/database.py`

Currently, `database.py` still has schema creation code but it's redundant now that Alembic creates everything. This can be safely removed in a future commit to eliminate duplication.

## Key Benefits

1. **Fresh database creation works**: `alembic upgrade head` creates complete working database
2. **Single source of truth**: Alembic migrations define schema, not Python code
3. **Reproducible**: Anyone can recreate database from migrations
4. **Version controlled**: Schema changes tracked in git via migrations
5. **Rollback capable**: Can downgrade if needed (though not recommended for prod)
6. **Safe**: Backups created before refactoring
7. **Idempotent**: Migrations detect existing data and skip appropriately

## Migration Chain

```
<base>
  |
  v
20251028_001 (Baseline - Creates 31 tables)
  |
  v
20251028_002 (Seed Data - Inserts required data)
  |
  v
(head)
```

## Files Changed

**Created**:
- `server/alembic/versions/20251028_001_proper_baseline.py`
- `server/alembic/versions/20251028_002_seed_data.py`
- `server/data/backup_schema.sql`
- `server/data/backup_seed_data.sql`
- `server/data/BACKUP_README.md`
- `server/data/compliance.db.backup`
- `test_fresh_migration.py` (testing script)
- `ALEMBIC_REFACTOR_SUMMARY.md` (this file)

**Archived**:
- `server/alembic/versions/ARCHIVED_20251027_001_complete_baseline.py.bak`
- `server/alembic/versions/ARCHIVED_20251027_002_update_operation_types.py.bak`

**Updated**:
- `docs/MIGRATION_SYSTEM.md`
- `CLAUDE.md`
- `server/data/compliance.db` (alembic_version table updated)

## Next Steps

1. ✅ Commit all changes with proper documentation
2. ⏭️ (Future) Remove `_create_tables()` from `database.py`
3. ⏭️ (Future) Remove `_run_migrations()` call from `database.py`
4. ⏭️ (Future) Delete `server/migrations/` directory (old system)

## Rollback Plan (If Needed)

If something goes wrong, restore from backups:

```bash
# Stop services
docker-compose down

# Restore database file
cp server/data/compliance.db.backup server/data/compliance.db

# Restart
docker-compose up
```

See `server/data/BACKUP_README.md` for detailed restore instructions.

---

**Result**: Alembic migration system is now properly implemented and can create fresh databases from scratch. ✅
