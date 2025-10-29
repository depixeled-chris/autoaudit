"""Test fresh database creation from Alembic migrations.

This script:
1. Creates a fresh test database
2. Runs Alembic migrations
3. Verifies all tables and seed data exist
4. Reports success/failure
"""
import sqlite3
import subprocess
import os
from pathlib import Path

# Paths
TEST_DB = "server/data/test_fresh.db"
PROJECT_ROOT = Path(__file__).parent

def cleanup():
    """Remove test database if it exists."""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
        print(f"✓ Removed existing test database: {TEST_DB}")

def run_migrations():
    """Run Alembic migrations on test database."""
    print("\n🔄 Running Alembic migrations...")

    # Set environment to use test database
    env = os.environ.copy()
    env['DATABASE_PATH'] = f'/app/data/test_fresh.db'

    result = subprocess.run(
        ['docker-compose', 'exec', '-T', 'server', 'alembic', 'upgrade', 'head'],
        capture_output=True,
        text=True,
        env=env
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    if result.returncode != 0:
        print(f"❌ Migration failed with code {result.returncode}")
        return False

    return True

def verify_schema():
    """Verify all tables and seed data exist."""
    print("\n🔍 Verifying database schema...")

    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()

    # Expected tables (excluding alembic_version and sqlite_sequence)
    expected_tables = [
        'users', 'refresh_tokens', 'states', 'projects', 'templates',
        'template_rules', 'urls', 'compliance_checks', 'violations',
        'visual_verifications', 'extraction_templates', 'llm_calls',
        'llm_logs', 'llm_model_config', 'legislation_sources',
        'legislation_digests', 'rules', 'rule_collisions', 'page_types',
        'preamble_templates', 'preambles', 'preamble_versions',
        'preamble_compositions', 'preamble_composition_deps',
        'default_page_type_preambles', 'project_page_type_preambles',
        'preamble_test_runs', 'preamble_version_performance',
        'schema_migrations'
    ]

    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    actual_tables = [row[0] for row in cursor.fetchall() if row[0] not in ('alembic_version', 'sqlite_sequence')]

    missing_tables = set(expected_tables) - set(actual_tables)
    extra_tables = set(actual_tables) - set(expected_tables)

    if missing_tables:
        print(f"❌ Missing tables: {missing_tables}")
        return False

    if extra_tables:
        print(f"⚠️  Extra tables: {extra_tables}")

    print(f"✓ All {len(expected_tables)} expected tables exist")

    # Check seed data
    cursor.execute("SELECT COUNT(*) FROM states")
    state_count = cursor.fetchone()[0]
    if state_count != 1:
        print(f"❌ Expected 1 state, found {state_count}")
        return False
    print("✓ States seeded (1 row)")

    cursor.execute("SELECT COUNT(*) FROM llm_model_config")
    config_count = cursor.fetchone()[0]
    if config_count != 5:
        print(f"❌ Expected 5 LLM configs, found {config_count}")
        return False
    print("✓ LLM model config seeded (5 rows)")

    cursor.execute("SELECT COUNT(*) FROM page_types")
    page_type_count = cursor.fetchone()[0]
    if page_type_count != 18:
        print(f"❌ Expected 18 page types, found {page_type_count}")
        return False
    print("✓ Page types seeded (18 rows)")

    cursor.execute("SELECT COUNT(*) FROM preamble_templates")
    template_count = cursor.fetchone()[0]
    if template_count != 1:
        print(f"❌ Expected 1 preamble template, found {template_count}")
        return False
    print("✓ Preamble templates seeded (1 row)")

    # Check Alembic version
    cursor.execute("SELECT version_num FROM alembic_version")
    version = cursor.fetchone()[0]
    print(f"✓ Alembic version: {version}")

    conn.close()
    return True

def main():
    """Run the test."""
    print("=" * 60)
    print("Testing Fresh Database Creation from Alembic")
    print("=" * 60)

    # Step 1: Cleanup
    cleanup()

    # Step 2: Run migrations
    if not run_migrations():
        print("\n❌ TEST FAILED: Migrations did not complete successfully")
        return 1

    # Step 3: Verify schema
    if not verify_schema():
        print("\n❌ TEST FAILED: Schema verification failed")
        return 1

    # Step 4: Cleanup
    print("\n🧹 Cleaning up...")
    cleanup()

    print("\n" + "=" * 60)
    print("✅ TEST PASSED: Fresh database creation successful!")
    print("=" * 60)
    return 0

if __name__ == '__main__':
    exit(main())
