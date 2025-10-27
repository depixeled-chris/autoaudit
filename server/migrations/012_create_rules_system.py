"""Create rules management system for atomic compliance requirements."""

import sqlite3


def up(conn: sqlite3.Connection):
    """Apply migration - create rules table."""
    cursor = conn.cursor()

    # Rules table - atomic compliance requirements extracted from legislation
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_code TEXT NOT NULL,
            legislation_source_id INTEGER,
            rule_text TEXT NOT NULL,
            applies_to_page_types TEXT,
            active INTEGER DEFAULT 1,
            approved INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (state_code) REFERENCES states(code),
            FOREIGN KEY (legislation_source_id) REFERENCES legislation_sources(id) ON DELETE CASCADE
        )
    """)

    # Create indexes for performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_rules_state_code
        ON rules(state_code)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_rules_legislation_source
        ON rules(legislation_source_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_rules_active
        ON rules(active)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_rules_approved
        ON rules(approved)
    """)

    conn.commit()


def down(conn: sqlite3.Connection):
    """Revert migration - drop rules table."""
    cursor = conn.cursor()

    # Drop indexes first
    cursor.execute("DROP INDEX IF EXISTS idx_rules_approved")
    cursor.execute("DROP INDEX IF EXISTS idx_rules_active")
    cursor.execute("DROP INDEX IF EXISTS idx_rules_legislation_source")
    cursor.execute("DROP INDEX IF EXISTS idx_rules_state_code")

    # Drop table
    cursor.execute("DROP TABLE IF EXISTS rules")

    conn.commit()
