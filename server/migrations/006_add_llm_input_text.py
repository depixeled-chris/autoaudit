"""Add llm_input_text column to compliance_checks table."""

import sqlite3
import logging

logger = logging.getLogger(__name__)


def up(conn: sqlite3.Connection):
    """Apply migration."""
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE compliance_checks ADD COLUMN llm_input_text TEXT")
        logger.info("Added llm_input_text column to compliance_checks table")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e).lower():
            logger.info("llm_input_text column already exists")
        else:
            raise


def down(conn: sqlite3.Connection):
    """Rollback migration."""
    # SQLite doesn't support DROP COLUMN easily, would need to recreate table
    raise NotImplementedError("Rollback not implemented for this migration")
