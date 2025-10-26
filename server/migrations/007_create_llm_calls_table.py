"""Create llm_calls table for tracking individual LLM API calls."""

import sqlite3
import logging

logger = logging.getLogger(__name__)


def up(conn: sqlite3.Connection):
    """Apply migration."""
    cursor = conn.cursor()

    # Create llm_calls table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS llm_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_id INTEGER NOT NULL,
            call_type TEXT NOT NULL,
            model TEXT NOT NULL,
            prompt_tokens INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (check_id) REFERENCES compliance_checks (id) ON DELETE CASCADE
        )
    """)

    # Create index for faster queries by check_id
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_llm_calls_check_id ON llm_calls(check_id)
    """)

    logger.info("Created llm_calls table and index")


def down(conn: sqlite3.Connection):
    """Rollback migration."""
    cursor = conn.cursor()
    cursor.execute("DROP INDEX IF EXISTS idx_llm_calls_check_id")
    cursor.execute("DROP TABLE IF EXISTS llm_calls")
    logger.info("Dropped llm_calls table and index")
