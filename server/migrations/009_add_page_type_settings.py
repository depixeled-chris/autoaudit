"""Add settings fields to page_types table."""

import sqlite3

def up(conn: sqlite3.Connection):
    """Apply migration."""
    cursor = conn.cursor()

    # Add new columns for page type settings
    cursor.execute("""
        ALTER TABLE page_types
        ADD COLUMN preamble TEXT
    """)

    cursor.execute("""
        ALTER TABLE page_types
        ADD COLUMN extraction_template TEXT
    """)

    cursor.execute("""
        ALTER TABLE page_types
        ADD COLUMN requires_llm_visual_confirmation BOOLEAN DEFAULT 0
    """)

    cursor.execute("""
        ALTER TABLE page_types
        ADD COLUMN requires_human_confirmation BOOLEAN DEFAULT 0
    """)

    # Set default preambles for existing page types
    cursor.execute("""
        UPDATE page_types
        SET preamble = 'Analyze this homepage for automotive dealership advertising compliance. Focus on disclosure requirements, font sizes, and layout positioning.'
        WHERE code = 'HOMEPAGE'
    """)

    cursor.execute("""
        UPDATE page_types
        SET preamble = 'Analyze this Vehicle Detail Page (VDP) for compliance. Pay special attention to pricing disclosures, finance terms, and required disclaimers.'
        WHERE code = 'VDP'
    """)

    cursor.execute("""
        UPDATE page_types
        SET preamble = 'Analyze this inventory listing page for compliance. Check that all vehicles display required disclosures consistently.'
        WHERE code = 'INVENTORY'
    """)

    cursor.execute("""
        UPDATE page_types
        SET preamble = 'Analyze this search results page for compliance. Verify that all listed vehicles include proper disclosures.'
        WHERE code = 'SRP'
    """)

    # Set VDP and HOMEPAGE to require LLM visual confirmation by default
    cursor.execute("""
        UPDATE page_types
        SET requires_llm_visual_confirmation = 1
        WHERE code IN ('VDP', 'HOMEPAGE')
    """)

    conn.commit()

def down(conn: sqlite3.Connection):
    """Revert migration."""
    # SQLite doesn't support DROP COLUMN in older versions
    # This is a simplified rollback - in production, you'd recreate the table
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE page_types_backup AS
        SELECT id, code, name, description, active, created_at, updated_at
        FROM page_types
    """)
    cursor.execute("DROP TABLE page_types")
    cursor.execute("ALTER TABLE page_types_backup RENAME TO page_types")
    conn.commit()
