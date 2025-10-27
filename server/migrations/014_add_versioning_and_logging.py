"""
Migration 013: Add versioning system and LLM logging

This migration adds:
1. Digest versioning (version, active columns)
2. Rules lineage (digest_id, modification tracking)
3. Rule collisions table
4. LLM logs table for cost tracking and audit
"""

import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def upgrade(conn: sqlite3.Connection):
    """Apply migration."""
    cursor = conn.cursor()

    logger.info("Starting migration 013: Add versioning and logging")

    # ========================================
    # 1. Enhance legislation_digests table
    # ========================================
    logger.info("Adding version and active columns to legislation_digests")

    cursor.execute("""
        ALTER TABLE legislation_digests
        ADD COLUMN version INTEGER DEFAULT 1
    """)

    cursor.execute("""
        ALTER TABLE legislation_digests
        ADD COLUMN active BOOLEAN DEFAULT 1
    """)

    # Create unique index: only one active digest per source
    cursor.execute("""
        CREATE UNIQUE INDEX idx_one_active_digest_per_source
        ON legislation_digests(legislation_source_id, active)
        WHERE active = 1
    """)

    # ========================================
    # 2. Enhance rules table
    # ========================================
    logger.info("Adding lineage and modification tracking to rules")

    cursor.execute("""
        ALTER TABLE rules
        ADD COLUMN legislation_digest_id INTEGER
    """)

    cursor.execute("""
        ALTER TABLE rules
        ADD COLUMN is_manually_modified BOOLEAN DEFAULT 0
    """)

    cursor.execute("""
        ALTER TABLE rules
        ADD COLUMN original_rule_text TEXT
    """)

    cursor.execute("""
        ALTER TABLE rules
        ADD COLUMN status TEXT DEFAULT 'active'
    """)

    cursor.execute("""
        ALTER TABLE rules
        ADD COLUMN supersedes_rule_id INTEGER
    """)

    # Note: SQLite doesn't support adding foreign keys to existing tables
    # We'll handle this in the next migration or recreate table if needed

    # Create indexes
    cursor.execute("""
        CREATE INDEX idx_rules_by_digest
        ON rules(legislation_digest_id)
    """)

    cursor.execute("""
        CREATE INDEX idx_rules_status
        ON rules(status)
    """)

    # ========================================
    # 3. Populate digest_id for existing rules
    # ========================================
    logger.info("Populating digest_id for existing rules")

    # Strategy: Match rules to digests by legislation_source_id
    # If multiple digests exist for a source, use the oldest one
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
    """)

    # Set original_rule_text to current rule_text for existing rules
    cursor.execute("""
        UPDATE rules
        SET original_rule_text = rule_text
        WHERE original_rule_text IS NULL
    """)

    # ========================================
    # 4. Create rule_collisions table
    # ========================================
    logger.info("Creating rule_collisions table")

    cursor.execute("""
        CREATE TABLE rule_collisions (
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
                REFERENCES rules(id) ON DELETE CASCADE,
            FOREIGN KEY (resolved_by)
                REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    cursor.execute("""
        CREATE INDEX idx_collisions_by_rule
        ON rule_collisions(rule_id)
    """)

    cursor.execute("""
        CREATE INDEX idx_collisions_by_existing
        ON rule_collisions(collides_with_rule_id)
    """)

    cursor.execute("""
        CREATE INDEX idx_collisions_pending
        ON rule_collisions(resolution)
        WHERE resolution IS NULL OR resolution = 'pending'
    """)

    # ========================================
    # 5. Create llm_logs table
    # ========================================
    logger.info("Creating llm_logs table")

    cursor.execute("""
        CREATE TABLE llm_logs (
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

            -- Cost Tracking
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    # Create indexes for common queries
    cursor.execute("""
        CREATE INDEX idx_llm_logs_endpoint
        ON llm_logs(api_endpoint)
    """)

    cursor.execute("""
        CREATE INDEX idx_llm_logs_operation
        ON llm_logs(operation_type)
    """)

    cursor.execute("""
        CREATE INDEX idx_llm_logs_model
        ON llm_logs(model)
    """)

    cursor.execute("""
        CREATE INDEX idx_llm_logs_created
        ON llm_logs(created_at)
    """)

    cursor.execute("""
        CREATE INDEX idx_llm_logs_user
        ON llm_logs(user_id)
    """)

    cursor.execute("""
        CREATE INDEX idx_llm_logs_cost
        ON llm_logs(total_cost_usd)
    """)

    cursor.execute("""
        CREATE INDEX idx_llm_logs_status
        ON llm_logs(status)
    """)

    conn.commit()
    logger.info("Migration 013 completed successfully")


def downgrade(conn: sqlite3.Connection):
    """Rollback migration."""
    cursor = conn.cursor()

    logger.info("Rolling back migration 013")

    # Drop tables
    cursor.execute("DROP TABLE IF EXISTS llm_logs")
    cursor.execute("DROP TABLE IF EXISTS rule_collisions")

    # Drop indexes
    cursor.execute("DROP INDEX IF EXISTS idx_rules_by_digest")
    cursor.execute("DROP INDEX IF EXISTS idx_rules_status")
    cursor.execute("DROP INDEX IF EXISTS idx_one_active_digest_per_source")

    # Note: SQLite doesn't support dropping columns easily
    # Would need to recreate tables to fully rollback
    # For now, just drop the new tables

    conn.commit()
    logger.info("Migration 013 rollback completed")


if __name__ == "__main__":
    # Test migration locally
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from core.config import DATABASE_PATH

    conn = sqlite3.connect(DATABASE_PATH)
    try:
        upgrade(conn)
        print("Migration 013 applied successfully")
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()
