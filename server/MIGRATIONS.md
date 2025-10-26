# Database Migration System

## Overview

AutoAudit uses a custom migration tracking system to manage database schema changes. Migrations are:
- **Versioned** - Each migration has a sequential version number
- **Tracked** - Applied migrations are recorded in the `schema_migrations` table
- **Idempotent** - Safe to run multiple times (columns are only added if they don't exist)
- **Automatic** - Run automatically on server startup

## Migration Tracking

All applied migrations are tracked in the `schema_migrations` table:

```sql
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## Current Migrations

| Version | Name | Description |
|---------|------|-------------|
| 1 | add_base_url | Add `base_url` column to projects table |
| 2 | add_screenshot_path | Add `screenshot_path` column to projects table |
| 3 | add_deleted_at | Add `deleted_at` column for soft deletes |
| 4 | add_token_tracking | Add token tracking columns to compliance_checks |
| 5 | add_visual_tokens | Add `tokens_used` column to visual_verifications |

## Running Migrations

### Automatic (Production)

Migrations run automatically when the database is initialized:

```python
from core.database import ComplianceDatabase

db = ComplianceDatabase("compliance.db")  # Migrations run automatically
```

### Manual (Development/Debugging)

Check migration status:
```bash
docker-compose exec server python -c "from core.migrations import get_migration_status; print(get_migration_status('/app/data/compliance.db'))"
```

Run pending migrations:
```bash
docker-compose exec server python -c "from core.migrations import run_migrations; run_migrations('/app/data/compliance.db')"
```

### Via Python

```python
from core.migrations import run_migrations, get_migration_status

# Check status
status = get_migration_status("compliance.db")
print(f"Applied: {status['applied_count']}")
print(f"Pending: {status['pending_count']}")

# Run migrations
run_migrations("compliance.db")
```

## Creating New Migrations

### 1. Add Migration Function

In `server/core/migrations.py`, create a new migration function:

```python
def migration_006_add_my_feature(conn):
    """Add my_column to my_table."""
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE my_table ADD COLUMN my_column TEXT")
        logger.info("Added my_column to my_table")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e).lower():
            logger.info("my_column already exists")
        else:
            raise
```

### 2. Register Migration

Add it to the `MIGRATIONS` list:

```python
MIGRATIONS = [
    Migration(1, "add_base_url", migration_001_add_base_url),
    Migration(2, "add_screenshot_path", migration_002_add_screenshot_path),
    Migration(3, "add_deleted_at", migration_003_add_deleted_at),
    Migration(4, "add_token_tracking", migration_004_add_token_tracking),
    Migration(5, "add_visual_tokens", migration_005_add_visual_tokens),
    Migration(6, "add_my_feature", migration_006_add_my_feature),  # NEW
]
```

### 3. Test Migration

Restart the server or run migrations manually:

```bash
docker-compose restart server
# OR
docker-compose exec server python -c "from core.migrations import run_migrations; run_migrations('/app/data/compliance.db')"
```

## Best Practices

1. **Version Numbers**: Always increment sequentially (never reuse or skip)
2. **Naming**: Use descriptive names (e.g., `add_user_roles`, not `migration_6`)
3. **Idempotency**: Always check if changes exist before applying
4. **Testing**: Test migrations on a copy of production data first
5. **Rollbacks**: Consider adding `down()` functions for complex migrations

## Migration Guidelines

### ✅ Good Migration

```python
def migration_007_add_status_column(conn):
    """Add status tracking to compliance checks."""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            ALTER TABLE compliance_checks
            ADD COLUMN status TEXT DEFAULT 'pending'
        """)
        logger.info("Added status column")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e).lower():
            logger.info("status column already exists")
        else:
            raise
```

### ❌ Bad Migration

```python
def migration_007(conn):  # Bad: No descriptive name
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE compliance_checks ADD COLUMN status TEXT")
    # Bad: No error handling (will crash if column exists)
    # Bad: No logging
```

## Troubleshooting

### Migration Failed

1. Check the error message in server logs
2. Verify the SQL syntax
3. Check if the table/column already exists
4. Test the migration on a fresh database

### Reset Migrations (Development Only)

**WARNING**: This deletes all migration history

```python
# Connect to database
import sqlite3
conn = sqlite3.connect("compliance.db")
cursor = conn.cursor()

# Delete migration history
cursor.execute("DROP TABLE IF EXISTS schema_migrations")
conn.commit()
conn.close()

# Restart server to re-run all migrations
```

### View Migration History

```sql
SELECT * FROM schema_migrations ORDER BY version;
```

## Future Enhancements

Potential improvements to the migration system:

1. **Rollback Support**: Implement `down()` functions for reversing migrations
2. **Migration Files**: Move migrations to separate files (e.g., `migrations/001_add_base_url.py`)
3. **CLI Tools**: Add management commands (`python manage.py migrate`, `python manage.py migration:create`)
4. **Dry Run**: Test migrations without applying them
5. **Checksum Validation**: Detect if migrations have been modified after being applied
