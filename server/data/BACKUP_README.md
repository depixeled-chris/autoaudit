# Database Backup Files

**Created**: 2025-10-28
**Purpose**: Failsafe for Alembic migration refactoring

## Files

- `backup_schema.sql` - Complete database schema (all CREATE TABLE, INDEX, TRIGGER statements)
- `backup_seed_data.sql` - Essential seed data (states, page_types, llm_model_config, preamble_templates)
- `compliance.db` - Original database file (if migration fails)

## How to Restore

### Full Restore from Backup

```bash
# Stop services
docker-compose down

# Remove corrupted database
rm server/data/compliance.db

# Restore from SQL backup
docker-compose up -d server
docker-compose exec server python -c "
import sqlite3
conn = sqlite3.connect('/app/data/compliance.db')

# Read and execute schema
with open('/app/data/backup_schema.sql', 'r') as f:
    schema = f.read()
    conn.executescript(schema)

# Read and execute seed data
with open('/app/data/backup_seed_data.sql', 'r') as f:
    seeds = f.read()
    conn.executescript(seeds)

conn.commit()
print('✓ Database restored from backup')
"
```

### Quick Copy Restore

```bash
# Just copy the original file back
cp server/data/compliance.db.backup server/data/compliance.db
```

## Seed Data Summary

**31 total tables**

Essential seed data (included in backup):
- **states**: 1 row (Oklahoma)
- **llm_model_config**: 5 rows (PARSE_LEGISLATION, GENERATE_RULES, DETECT_COLLISIONS, GENERATE_PREAMBLE, COMPLIANCE_CHECK)
- **page_types**: 18 rows (HOMEPAGE, VDP, INVENTORY, FINANCING, LEASE, SERVICE, ABOUT_US, CONTACT, STAFF, REVIEWS, BLOG, SPECIALS, NEW_INVENTORY, USED_INVENTORY, TRADE_IN, SCHEDULE_SERVICE, PARTS, CAREERS)
- **preamble_templates**: 1 row (Standard Hierarchical composition template)

## After Restore

1. Mark Alembic as current:
```bash
docker-compose exec server python -c "
import sqlite3
conn = sqlite3.connect('/app/data/compliance.db')
conn.execute(\"INSERT OR REPLACE INTO alembic_version (version_num) VALUES ('20251027_002')\")
conn.commit()
"
```

2. Restart services:
```bash
docker-compose restart
```
