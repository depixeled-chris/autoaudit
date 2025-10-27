"""Apply preamble system schema directly."""

import sqlite3
import sys
from pathlib import Path

def apply_schema(db_path='/app/data/compliance.db'):
    """Apply all preamble system tables."""
    conn = sqlite3.Connection(db_path)
    cursor = conn.cursor()

    print("Creating preamble system schema...")

    # Legislation sources
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS legislation_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_code TEXT NOT NULL,
            statute_number TEXT NOT NULL,
            title TEXT NOT NULL,
            full_text TEXT NOT NULL,
            source_url TEXT,
            effective_date DATE,
            sunset_date DATE,
            last_verified_date DATE,
            applies_to_page_types TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (state_code) REFERENCES states(code),
            UNIQUE(state_code, statute_number)
        )
    """)
    print("✓ legislation_sources")

    # Legislation digests
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS legislation_digests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            legislation_source_id INTEGER NOT NULL,
            digest_type TEXT NOT NULL CHECK(digest_type IN ('universal', 'page_specific')),
            page_type_code TEXT,
            interpreted_requirements TEXT,
            created_by INTEGER,
            reviewed_by INTEGER,
            last_review_date TIMESTAMP,
            approved BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (legislation_source_id) REFERENCES legislation_sources(id),
            FOREIGN KEY (page_type_code) REFERENCES page_types(code)
        )
    """)
    print("✓ legislation_digests")

    # Preamble templates
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preamble_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            template_structure TEXT NOT NULL,
            is_default BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ preamble_templates")

    # Insert default template
    cursor.execute("""
        INSERT OR IGNORE INTO preamble_templates (name, description, template_structure, is_default)
        VALUES (?, ?, ?, ?)
    """, (
        'Standard Hierarchical',
        'Standard composition: Universal → State → Page Type → Project',
        '''# UNIVERSAL COMPLIANCE PRINCIPLES
{{ universal_preamble }}

# STATE-SPECIFIC REQUIREMENTS: {{ state_code }}
{{ state_preamble }}

# PAGE TYPE GUIDANCE: {{ page_type }}
{{ page_type_preamble }}

{% if project_preamble %}
# PROJECT-SPECIFIC CONTEXT
{{ project_preamble }}
{% endif %}

# CITATION FORMAT REQUIREMENTS
CRITICAL: Format all citations as structured JSON:
{
  "violations": [
    {
      "statute": "Full statute reference",
      "rule": "Plain language requirement",
      "severity": "critical|important|minor",
      "location": "Where violation occurs",
      "evidence": "Specific violating content",
      "recommendation": "How to fix"
    }
  ]
}''',
        1
    ))
    print("✓ default template inserted")

    # Preambles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preambles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            machine_name TEXT NOT NULL UNIQUE,
            scope TEXT NOT NULL CHECK(scope IN ('universal', 'state', 'page_type', 'project')),
            page_type_code TEXT,
            state_code TEXT,
            project_id INTEGER,
            created_via TEXT NOT NULL CHECK(created_via IN ('config', 'project_override')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (page_type_code) REFERENCES page_types(code),
            FOREIGN KEY (state_code) REFERENCES states(code),
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """)
    print("✓ preambles")

    # Preamble versions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preamble_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            preamble_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            preamble_text TEXT NOT NULL,
            change_summary TEXT,
            status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft', 'active', 'retired')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (preamble_id) REFERENCES preambles(id),
            UNIQUE(preamble_id, version_number)
        )
    """)
    print("✓ preamble_versions")

    # Performance tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preamble_version_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            preamble_version_id INTEGER NOT NULL,
            test_runs_count INTEGER DEFAULT 0,
            avg_score REAL,
            score_stddev REAL,
            avg_confidence REAL,
            false_positive_rate REAL,
            false_negative_rate REAL,
            avg_cost REAL,
            avg_duration_seconds REAL,
            last_tested_at TIMESTAMP,
            FOREIGN KEY (preamble_version_id) REFERENCES preamble_versions(id),
            UNIQUE(preamble_version_id)
        )
    """)
    print("✓ preamble_version_performance")

    # Test runs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preamble_test_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            preamble_version_id INTEGER NOT NULL,
            url_id INTEGER NOT NULL,
            run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            score_achieved REAL,
            violations_found TEXT,
            confidence_score REAL,
            token_count INTEGER,
            cost REAL,
            duration_seconds REAL,
            model_used TEXT,
            false_positive BOOLEAN,
            false_negative BOOLEAN,
            FOREIGN KEY (preamble_version_id) REFERENCES preamble_versions(id),
            FOREIGN KEY (url_id) REFERENCES urls(id)
        )
    """)
    print("✓ preamble_test_runs")

    # Composition cache
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preamble_compositions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            composition_hash TEXT NOT NULL UNIQUE,
            template_id INTEGER NOT NULL,
            universal_version_id INTEGER,
            state_version_id INTEGER,
            page_type_version_id INTEGER,
            project_version_id INTEGER,
            composed_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            hit_count INTEGER DEFAULT 0,
            FOREIGN KEY (template_id) REFERENCES preamble_templates(id),
            FOREIGN KEY (universal_version_id) REFERENCES preamble_versions(id),
            FOREIGN KEY (state_version_id) REFERENCES preamble_versions(id),
            FOREIGN KEY (page_type_version_id) REFERENCES preamble_versions(id),
            FOREIGN KEY (project_version_id) REFERENCES preamble_versions(id)
        )
    """)
    print("✓ preamble_compositions")

    # Composition dependencies
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preamble_composition_deps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            composition_id INTEGER NOT NULL,
            depends_on_version_id INTEGER NOT NULL,
            FOREIGN KEY (composition_id) REFERENCES preamble_compositions(id) ON DELETE CASCADE,
            FOREIGN KEY (depends_on_version_id) REFERENCES preamble_versions(id) ON DELETE CASCADE,
            UNIQUE(composition_id, depends_on_version_id)
        )
    """)
    print("✓ preamble_composition_deps")

    # Default assignments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS default_page_type_preambles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_type_code TEXT NOT NULL,
            preamble_id INTEGER NOT NULL,
            active_version_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (page_type_code) REFERENCES page_types(code),
            FOREIGN KEY (preamble_id) REFERENCES preambles(id),
            FOREIGN KEY (active_version_id) REFERENCES preamble_versions(id),
            UNIQUE(page_type_code)
        )
    """)
    print("✓ default_page_type_preambles")

    # Project overrides
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_page_type_preambles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            page_type_code TEXT NOT NULL,
            preamble_id INTEGER NOT NULL,
            active_version_id INTEGER NOT NULL,
            override_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (page_type_code) REFERENCES page_types(code),
            FOREIGN KEY (preamble_id) REFERENCES preambles(id),
            FOREIGN KEY (active_version_id) REFERENCES preamble_versions(id),
            UNIQUE(project_id, page_type_code)
        )
    """)
    print("✓ project_page_type_preambles")

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_preamble_versions_preamble ON preamble_versions(preamble_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_preamble_versions_status ON preamble_versions(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_preamble_test_runs_version ON preamble_test_runs(preamble_version_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_preamble_compositions_hash ON preamble_compositions(composition_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_legislation_sources_state ON legislation_sources(state_code)")
    print("✓ indexes created")

    conn.commit()
    conn.close()
    print("\n✅ Preamble system schema applied successfully!")

if __name__ == '__main__':
    apply_schema()
