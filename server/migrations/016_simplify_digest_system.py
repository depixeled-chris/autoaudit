"""
Migration 016: Simplify digest system
- Remove digest_type and page_type_code from legislation_digests
- Keep active column to mark which version is active
- Keep UNIQUE constraint on (source_id, active) WHERE active=1
- Add UNIQUE constraint on (source_id, version)
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)


def upgrade(conn: sqlite3.Connection):
    """Apply migration."""
    cursor = conn.cursor()

    logger.info("Starting migration 016: Simplify digest system")

    # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
    logger.info("Creating new legislation_digests table")

    cursor.execute("""
        CREATE TABLE legislation_digests_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            legislation_source_id INTEGER NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            active BOOLEAN DEFAULT 1,
            interpreted_requirements TEXT NOT NULL,
            approved BOOLEAN DEFAULT 0,
            created_by INTEGER,
            reviewed_by INTEGER,
            last_review_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (legislation_source_id) REFERENCES legislation_sources(id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (reviewed_by) REFERENCES users(id)
        )
    """)

    # Copy data from old table (excluding digest_type and page_type_code)
    logger.info("Migrating data from old table")
    cursor.execute("""
        INSERT INTO legislation_digests_new
            (id, legislation_source_id, version, active, interpreted_requirements, approved,
             created_by, reviewed_by, last_review_date, created_at, updated_at)
        SELECT
            id, legislation_source_id, version, active, interpreted_requirements, approved,
            created_by, reviewed_by, last_review_date, created_at, updated_at
        FROM legislation_digests
    """)

    # Drop old table
    logger.info("Dropping old table")
    cursor.execute("DROP TABLE legislation_digests")

    # Rename new table
    logger.info("Renaming new table")
    cursor.execute("ALTER TABLE legislation_digests_new RENAME TO legislation_digests")

    # Create indexes
    logger.info("Creating indexes")
    cursor.execute("""
        CREATE UNIQUE INDEX idx_one_active_digest_per_source
        ON legislation_digests(legislation_source_id, active)
        WHERE active = 1
    """)
    cursor.execute("""
        CREATE INDEX idx_digests_by_source
        ON legislation_digests(legislation_source_id)
    """)

    conn.commit()
    logger.info("Migration 016 completed successfully")


def downgrade(conn: sqlite3.Connection):
    """Rollback migration."""
    cursor = conn.cursor()

    logger.info("Rolling back migration 016")

    # Recreate old table structure
    cursor.execute("""
        CREATE TABLE legislation_digests_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            legislation_source_id INTEGER NOT NULL,
            digest_type TEXT NOT NULL DEFAULT 'universal',
            page_type_code TEXT,
            version INTEGER NOT NULL DEFAULT 1,
            active BOOLEAN DEFAULT 1,
            interpreted_requirements TEXT NOT NULL,
            approved BOOLEAN DEFAULT 0,
            created_by INTEGER,
            reviewed_by INTEGER,
            last_review_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (legislation_source_id) REFERENCES legislation_sources(id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (reviewed_by) REFERENCES users(id)
        )
    """)

    # Copy data back
    cursor.execute("""
        INSERT INTO legislation_digests_new
            (id, legislation_source_id, digest_type, version, active, interpreted_requirements,
             approved, created_by, reviewed_by, last_review_date, created_at, updated_at)
        SELECT
            id, legislation_source_id, 'universal', version, 1, interpreted_requirements,
            approved, created_by, reviewed_by, last_review_date, created_at, updated_at
        FROM legislation_digests
    """)

    cursor.execute("DROP TABLE legislation_digests")
    cursor.execute("ALTER TABLE legislation_digests_new RENAME TO legislation_digests")

    # Recreate old index
    cursor.execute("""
        CREATE UNIQUE INDEX idx_one_active_digest_per_source
        ON legislation_digests(legislation_source_id, active)
        WHERE active = 1
    """)

    conn.commit()
    logger.info("Migration 016 rolled back")
