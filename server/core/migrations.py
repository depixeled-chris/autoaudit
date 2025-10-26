"""Database migration system."""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Callable
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Migration:
    """Represents a single database migration."""

    def __init__(self, version: int, name: str, up: Callable, down: Callable = None):
        """
        Initialize migration.

        Args:
            version: Migration version number (e.g., 1, 2, 3)
            name: Descriptive name (e.g., "add_token_tracking")
            up: Function to apply migration
            down: Function to rollback migration (optional)
        """
        self.version = version
        self.name = name
        self.up = up
        self.down = down

    def __repr__(self):
        return f"Migration(v{self.version}: {self.name})"


class MigrationRunner:
    """Runs and tracks database migrations."""

    def __init__(self, db_path: str):
        """
        Initialize migration runner.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._ensure_migrations_table()

    def _ensure_migrations_table(self):
        """Create migrations tracking table if it doesn't exist."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
        logger.info("Migrations table ready")

    def get_applied_versions(self) -> List[int]:
        """Get list of applied migration versions."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
        return [row[0] for row in cursor.fetchall()]

    def is_applied(self, version: int) -> bool:
        """Check if a migration version has been applied."""
        return version in self.get_applied_versions()

    def apply_migration(self, migration: Migration):
        """
        Apply a single migration.

        Args:
            migration: Migration to apply
        """
        if self.is_applied(migration.version):
            logger.info(f"Migration {migration.version} already applied, skipping")
            return

        logger.info(f"Applying migration {migration.version}: {migration.name}")

        try:
            # Run migration
            migration.up(self.conn)

            # Record migration
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO schema_migrations (version, name)
                VALUES (?, ?)
            """, (migration.version, migration.name))
            self.conn.commit()

            logger.info(f"✓ Migration {migration.version} applied successfully")

        except Exception as e:
            self.conn.rollback()
            logger.error(f"✗ Migration {migration.version} failed: {str(e)}")
            raise

    def rollback_migration(self, migration: Migration):
        """
        Rollback a single migration.

        Args:
            migration: Migration to rollback
        """
        if not self.is_applied(migration.version):
            logger.info(f"Migration {migration.version} not applied, nothing to rollback")
            return

        if not migration.down:
            raise ValueError(f"Migration {migration.version} has no rollback function")

        logger.info(f"Rolling back migration {migration.version}: {migration.name}")

        try:
            # Run rollback
            migration.down(self.conn)

            # Remove migration record
            cursor = self.conn.cursor()
            cursor.execute("""
                DELETE FROM schema_migrations WHERE version = ?
            """, (migration.version,))
            self.conn.commit()

            logger.info(f"✓ Migration {migration.version} rolled back successfully")

        except Exception as e:
            self.conn.rollback()
            logger.error(f"✗ Rollback of migration {migration.version} failed: {str(e)}")
            raise

    def run_migrations(self, migrations: List[Migration], target_version: int = None):
        """
        Run all pending migrations up to target version.

        Args:
            migrations: List of migrations to run
            target_version: Stop at this version (default: run all)
        """
        applied = self.get_applied_versions()
        pending = [m for m in migrations if m.version not in applied]

        if target_version:
            pending = [m for m in pending if m.version <= target_version]

        if not pending:
            logger.info("No pending migrations")
            return

        logger.info(f"Running {len(pending)} pending migration(s)")

        for migration in sorted(pending, key=lambda m: m.version):
            self.apply_migration(migration)

        logger.info("All migrations completed")

    def get_status(self, migrations: List[Migration]) -> Dict:
        """
        Get migration status.

        Args:
            migrations: All available migrations

        Returns:
            Dictionary with migration status
        """
        applied = self.get_applied_versions()
        pending = [m for m in migrations if m.version not in applied]

        return {
            'applied_count': len(applied),
            'pending_count': len(pending),
            'applied_versions': applied,
            'pending_migrations': [{'version': m.version, 'name': m.name} for m in pending],
            'latest_version': max(applied) if applied else 0
        }

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Migration runner closed")


# =============================================================================
# Migration Definitions
# =============================================================================

def migration_001_add_base_url(conn):
    """Add base_url column to projects table."""
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE projects ADD COLUMN base_url TEXT")
        logger.info("Added base_url column to projects table")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e).lower():
            logger.info("base_url column already exists")
        else:
            raise


def migration_002_add_screenshot_path(conn):
    """Add screenshot_path column to projects table."""
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE projects ADD COLUMN screenshot_path TEXT")
        logger.info("Added screenshot_path column to projects table")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e).lower():
            logger.info("screenshot_path column already exists")
        else:
            raise


def migration_003_add_deleted_at(conn):
    """Add deleted_at column to projects table for soft deletes."""
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE projects ADD COLUMN deleted_at TIMESTAMP")
        logger.info("Added deleted_at column to projects table")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e).lower():
            logger.info("deleted_at column already exists")
        else:
            raise


def migration_004_add_token_tracking(conn):
    """Add token tracking columns to compliance_checks table."""
    cursor = conn.cursor()

    columns = [
        ('text_analysis_tokens', 'INTEGER DEFAULT 0'),
        ('visual_tokens', 'INTEGER DEFAULT 0'),
        ('total_tokens', 'INTEGER DEFAULT 0')
    ]

    for column_name, column_type in columns:
        try:
            cursor.execute(f"ALTER TABLE compliance_checks ADD COLUMN {column_name} {column_type}")
            logger.info(f"Added {column_name} column to compliance_checks table")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e).lower():
                logger.info(f"{column_name} column already exists")
            else:
                raise


def migration_005_add_visual_tokens(conn):
    """Add tokens_used column to visual_verifications table."""
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE visual_verifications ADD COLUMN tokens_used INTEGER DEFAULT 0")
        logger.info("Added tokens_used column to visual_verifications table")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e).lower():
            logger.info("tokens_used column already exists")
        else:
            raise


def migration_006_add_llm_input_text(conn):
    """Add llm_input_text column to compliance_checks table."""
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE compliance_checks ADD COLUMN llm_input_text TEXT")
        logger.info("Added llm_input_text column to compliance_checks table")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e).lower():
            logger.info("llm_input_text column already exists")
        else:
            raise


def migration_007_create_llm_calls_table(conn):
    """Create llm_calls table for tracking individual LLM API calls."""
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


# All migrations in order
MIGRATIONS = [
    Migration(1, "add_base_url", migration_001_add_base_url),
    Migration(2, "add_screenshot_path", migration_002_add_screenshot_path),
    Migration(3, "add_deleted_at", migration_003_add_deleted_at),
    Migration(4, "add_token_tracking", migration_004_add_token_tracking),
    Migration(5, "add_visual_tokens", migration_005_add_visual_tokens),
    Migration(6, "add_llm_input_text", migration_006_add_llm_input_text),
    Migration(7, "create_llm_calls_table", migration_007_create_llm_calls_table),
]


def run_migrations(db_path: str):
    """
    Run all pending migrations.

    Args:
        db_path: Path to SQLite database
    """
    runner = MigrationRunner(db_path)
    try:
        runner.run_migrations(MIGRATIONS)
    finally:
        runner.close()


def get_migration_status(db_path: str) -> Dict:
    """
    Get migration status.

    Args:
        db_path: Path to SQLite database

    Returns:
        Migration status dictionary
    """
    runner = MigrationRunner(db_path)
    try:
        return runner.get_status(MIGRATIONS)
    finally:
        runner.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python migrations.py [status|migrate] [db_path]")
        sys.exit(1)

    command = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else "compliance.db"

    if command == "status":
        status = get_migration_status(db_path)
        print(f"\n=== Migration Status ===")
        print(f"Database: {db_path}")
        print(f"Applied: {status['applied_count']} migrations")
        print(f"Pending: {status['pending_count']} migrations")
        print(f"Latest version: {status['latest_version']}")

        if status['pending_migrations']:
            print(f"\nPending migrations:")
            for m in status['pending_migrations']:
                print(f"  - v{m['version']}: {m['name']}")

    elif command == "migrate":
        run_migrations(db_path)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
