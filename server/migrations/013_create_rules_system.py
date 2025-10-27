"""
Migration 013: Create rules system

Replace legislation digests with a cleaner rules system:
- Rules are atomic compliance requirements
- Tied to legislation sources
- Can be re-digested easily
- State-specific with page type targeting
"""

def up(cursor):
    """Apply migration."""

    # Create rules table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_code TEXT NOT NULL,
            legislation_source_id INTEGER,
            rule_text TEXT NOT NULL,
            applies_to_page_types TEXT,
            active BOOLEAN DEFAULT 1,
            approved BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (legislation_source_id) REFERENCES legislation_sources(id) ON DELETE CASCADE
        )
    """)

    # Create indexes for efficient queries
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


def down(cursor):
    """Rollback migration."""
    cursor.execute("DROP TABLE IF EXISTS rules")
