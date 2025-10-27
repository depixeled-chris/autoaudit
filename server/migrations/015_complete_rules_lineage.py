"""
Migration 015: Complete rules lineage system

This migration completes the rules lineage system by adding:
1. Missing lineage columns to rules table (5 columns)
2. rule_collisions table for collision detection
3. llm_logs table for comprehensive LLM cost tracking

Note: legislation_digests already has version and active columns from a previous migration.
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)


def upgrade(conn: sqlite3.Connection):
    """Apply migration."""
    cursor = conn.cursor()

    logger.info("Starting migration 015: Complete rules lineage system")

    # ========================================
    # 1. Add missing lineage columns to rules table
    # ========================================
    logger.info("Adding lineage columns to rules table")

    columns_to_add = [
        ('legislation_digest_id', 'INTEGER'),
        ('is_manually_modified', 'BOOLEAN DEFAULT 0'),
        ('original_rule_text', 'TEXT'),
        ('status', 'TEXT DEFAULT "active"'),
        ('supersedes_rule_id', 'INTEGER'),
    ]

    for column_name, column_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE rules ADD COLUMN {column_name} {column_type}")
            logger.info(f"  Added column: {column_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                logger.info(f"  Column {column_name} already exists, skipping")
            else:
                raise

    # Create indexes
    try:
        cursor.execute("""
            CREATE INDEX idx_rules_by_digest
            ON rules(legislation_digest_id)
        """)
        logger.info("  Created index on legislation_digest_id")
    except sqlite3.OperationalError as e:
        if "already exists" in str(e).lower():
            logger.info("  Index idx_rules_by_digest already exists")

    try:
        cursor.execute("""
            CREATE INDEX idx_rules_status
            ON rules(status)
        """)
        logger.info("  Created index on status")
    except sqlite3.OperationalError as e:
        if "already exists" in str(e).lower():
            logger.info("  Index idx_rules_status already exists")

    # ========================================
    # 2. Populate digest_id for existing rules
    # ========================================
    logger.info("Populating digest_id for existing rules")

    # Strategy: Match rules to digests by legislation_source_id
    # If multiple digests exist for a source, use the active one (or oldest if none active)
    cursor.execute("""
        UPDATE rules
        SET legislation_digest_id = (
            SELECT id
            FROM legislation_digests
            WHERE legislation_digests.legislation_source_id = rules.legislation_source_id
            AND legislation_digests.active = 1
            LIMIT 1
        )
        WHERE legislation_source_id IS NOT NULL
        AND legislation_digest_id IS NULL
    """)

    # For rules without an active digest, use the oldest digest
    cursor.execute("""
        UPDATE rules
        SET legislation_digest_id = (
            SELECT id
            FROM legislation_digests
            WHERE legislation_digests.legislation_source_id = rules.legislation_source_id
            ORDER BY created_at ASC
            LIMIT 1
        )
        WHERE legislation_source_id IS NOT NULL
        AND legislation_digest_id IS NULL
    """)

    # Set original_rule_text to current rule_text for existing rules
    cursor.execute("""
        UPDATE rules
        SET original_rule_text = rule_text
        WHERE original_rule_text IS NULL
    """)

    logger.info("  Populated lineage data for existing rules")

    # ========================================
    # 3. Create rule_collisions table
    # ========================================
    logger.info("Creating rule_collisions table")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rule_collisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id INTEGER NOT NULL,
            collides_with_rule_id INTEGER NOT NULL,
            collision_type TEXT NOT NULL CHECK(
                collision_type IN ('duplicate', 'semantic', 'conflict', 'overlap', 'supersedes')
            ),
            confidence REAL,
            ai_explanation TEXT,
            resolution TEXT CHECK(
                resolution IS NULL OR
                resolution IN ('keep_both', 'keep_existing', 'keep_new', 'merge', 'pending')
            ),
            resolved_by INTEGER,
            resolved_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (rule_id)
                REFERENCES rules(id) ON DELETE CASCADE,
            FOREIGN KEY (collides_with_rule_id)
                REFERENCES rules(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_collisions_by_rule
        ON rule_collisions(rule_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_collisions_by_existing
        ON rule_collisions(collides_with_rule_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_collisions_pending
        ON rule_collisions(resolution)
        WHERE resolution IS NULL OR resolution = 'pending'
    """)

    logger.info("  Created rule_collisions table with indexes")

    # ========================================
    # 4. Create llm_logs table
    # ========================================
    logger.info("Creating llm_logs table")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS llm_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Request Context
            api_endpoint TEXT NOT NULL,
            operation_type TEXT NOT NULL,
            user_id INTEGER,

            -- LLM Details
            model TEXT NOT NULL,
            provider TEXT DEFAULT 'openai',

            -- Input/Output
            input_text TEXT NOT NULL,
            output_text TEXT NOT NULL,
            input_tokens INTEGER NOT NULL,
            output_tokens INTEGER NOT NULL,
            total_tokens INTEGER NOT NULL,

            -- Cost Tracking (USD)
            input_cost_usd REAL,
            output_cost_usd REAL,
            total_cost_usd REAL,

            -- Performance
            duration_ms INTEGER,

            -- Status
            status TEXT NOT NULL DEFAULT 'success' CHECK(
                status IN ('success', 'error', 'timeout')
            ),
            error_message TEXT,

            -- Metadata
            request_id TEXT,
            related_entity_type TEXT,
            related_entity_id INTEGER,

            -- Timestamps
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes for common queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_llm_logs_endpoint
        ON llm_logs(api_endpoint)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_llm_logs_operation
        ON llm_logs(operation_type)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_llm_logs_model
        ON llm_logs(model)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_llm_logs_created
        ON llm_logs(created_at)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_llm_logs_user
        ON llm_logs(user_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_llm_logs_cost
        ON llm_logs(total_cost_usd)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_llm_logs_status
        ON llm_logs(status)
    """)

    logger.info("  Created llm_logs table with indexes")

    conn.commit()
    logger.info("✓ Migration 015 completed successfully")


def downgrade(conn: sqlite3.Connection):
    """Rollback migration."""
    cursor = conn.cursor()

    logger.info("Rolling back migration 015")

    # Drop tables
    cursor.execute("DROP TABLE IF EXISTS llm_logs")
    cursor.execute("DROP TABLE IF EXISTS rule_collisions")

    # Drop indexes
    cursor.execute("DROP INDEX IF EXISTS idx_rules_by_digest")
    cursor.execute("DROP INDEX IF EXISTS idx_rules_status")

    # Note: SQLite doesn't support dropping columns easily
    # Would need to recreate table to fully rollback
    # For now, just drop the new tables

    conn.commit()
    logger.info("Migration 015 rollback completed")


if __name__ == "__main__":
    # Test migration locally
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from core.config import DATABASE_PATH

    conn = sqlite3.connect(DATABASE_PATH)
    try:
        upgrade(conn)
        print("✓ Migration 015 applied successfully")
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()
