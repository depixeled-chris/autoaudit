# Migration System Documentation

## ✅ RESOLVED: Single Alembic System (2025-10-28)

**Status**: Properly implemented. Alembic can now create fresh databases from scratch with all schema and seed data.

### Current System: Alembic (ACTIVE)
- **Location**: `server/alembic/versions/*.py` files
- **Pattern**: Standard Alembic format with `upgrade()` and `downgrade()` functions
- **Auto-runs**: NO - Run via `alembic upgrade head`
- **Docker**: ✅ Mounted as part of `./server:/app`
- **Tracking**: Alembic's `alembic_version` table
- **Status**: ✅ ACTIVE - CAN CREATE FRESH DATABASES

### Applied Alembic Migrations
- **20251028_001**: **Proper baseline** - Creates ALL 31 tables from scratch with indexes
- **20251028_002**: **Seed data** - Inserts essential data (states, llm_model_config, page_types, preamble_templates)

### Previous Migrations (ARCHIVED - 2025-10-28)
- **20251027_001**: NO-OP baseline (ARCHIVED - only checked if tables existed, created nothing)
- **20251027_002**: Operation types update (ARCHIVED - functionality moved to seed data migration)

### Database Backups
**Location**: `server/data/`
- `backup_schema.sql` - Complete schema dump (all CREATE statements)
- `backup_seed_data.sql` - Seed data INSERT statements
- `compliance.db.backup` - Full database file backup
- `BACKUP_README.md` - Restore instructions

**These backups were created before Alembic refactoring as a failsafe.**

### System 1: Legacy Inline System (`core/migrations.py`) - DELETED
- **Location**: `server/core/migrations.py` (DELETED 2025-10-28)
- **Pattern**: Inline functions with `Migration(version, name, func)` registration
- **Status**: ⚠️ DELETED - File no longer exists
- **Historical Migrations**:
  - v1-7: Various column additions (base_url, screenshot_path, deleted_at, token tracking, etc.)
  - v8: add_versioning_and_logging (adds digest versioning, INCOMPLETE for rules)

### System 2: External Manual Files (`server/migrations/`) - DEPRECATED
- **Location**: `server/migrations/*.py` files (DEPRECATED)
- **Pattern**: Separate files with `upgrade(conn)` and `downgrade(conn)` functions
- **Status**: ❌ DEPRECATED - Content consolidated into Alembic baseline
- **Historical Files**:
  - 006-007: Duplicates of System 1 migrations
  - 008-010: Page types system
  - 011: Preamble system
  - 012-013: Rules system
  - 014: Versioning and logging (failed)
  - 015: Complete rules lineage (applied)

## Current Database State (Updated 2025-10-28)

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

### For New Migrations (Use Alembic)

1. **Create migration file**:
   ```bash
   # From project root or inside Docker
   docker-compose exec server alembic revision -m "your_migration_description"

   # This creates: server/alembic/versions/YYYYMMDD_XXX_your_migration_description.py
   ```

2. **Edit the generated file**:
   ```python
   """Brief description

   Revision ID: auto_generated_id
   Revises: previous_revision_id
   Create Date: YYYY-MM-DD
   """
   from typing import Sequence, Union
   from alembic import op
   import sqlalchemy as sa

   revision: str = 'auto_generated_id'
   down_revision: Union[str, None] = 'previous_revision_id'
   branch_labels: Union[str, Sequence[str], None] = None
   depends_on: Union[str, Sequence[str], None] = None

   def upgrade() -> None:
       """Apply migration."""
       # Use op.add_column(), op.create_table(), etc.
       op.add_column('table_name', sa.Column('new_column', sa.String(), nullable=True))

   def downgrade() -> None:
       """Rollback migration."""
       op.drop_column('table_name', 'new_column')
   ```

3. **Run migration**:
   ```bash
   # Apply all pending migrations
   docker-compose exec server alembic upgrade head

   # Or apply specific number of migrations
   docker-compose exec server alembic upgrade +1
   ```

4. **Verify**:
   ```bash
   # Check current version
   docker-compose exec server alembic current

   # Check migration history
   docker-compose exec server alembic history

   # Verify database schema
   docker-compose exec server python -c "
   import sqlite3
   conn = sqlite3.connect('/app/data/compliance.db')
   cursor = conn.cursor()
   cursor.execute('PRAGMA table_info(your_table)')
   print(cursor.fetchall())
   "
   ```

### Common Alembic Commands

```bash
# Check current migration version
alembic current

# Show migration history
alembic history

# Upgrade to latest
alembic upgrade head

# Downgrade one migration
alembic downgrade -1

# Show pending migrations
alembic current
alembic show head
```

## Migration Pattern Reference

### Alembic Pattern (Current)

```python
"""Add new feature table

Revision ID: 20251028_001
Revises: 20251027_002
Create Date: 2025-10-28
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20251028_001'
down_revision: Union[str, None] = '20251027_002'

def upgrade() -> None:
    """Add new table and columns."""
    # Create table
    op.create_table(
        'new_feature',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Add column to existing table
    op.add_column('existing_table', sa.Column('new_field', sa.String(), nullable=True))

    # Create index
    op.create_index('idx_new_feature_name', 'new_feature', ['name'])

def downgrade() -> None:
    """Remove table and columns."""
    op.drop_index('idx_new_feature_name')
    op.drop_column('existing_table', 'new_field')
    op.drop_table('new_feature')
```

### Legacy Patterns (Historical Reference Only)

**System 1** (deleted): Inline functions in `core/migrations.py`
**System 2** (deprecated): Manual `upgrade(conn)` in `server/migrations/`

Both systems are no longer used. All new migrations use Alembic.
