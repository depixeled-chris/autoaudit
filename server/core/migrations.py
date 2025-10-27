"""Database migration system with auto-discovery."""

import sqlite3
import logging
import importlib.util
import sys
from pathlib import Path
from typing import List, Dict, Callable, Optional
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


def migration_008_add_versioning_and_logging(conn):
    """
    Add versioning system and LLM logging.

    This migration adds:
    1. Digest versioning (version, active columns)
    2. Rules lineage (digest_id, modification tracking)
    3. Rule collisions table
    4. LLM logs table for cost tracking and audit
    """
    cursor = conn.cursor()

    logger.info("Starting migration 008: Add versioning and logging")

    # ========================================
    # 1. Enhance legislation_digests table
    # ========================================
    logger.info("Adding version and active columns to legislation_digests")

    try:
        cursor.execute("ALTER TABLE legislation_digests ADD COLUMN version INTEGER DEFAULT 1")
        logger.info("Added version column")
    except sqlite3.OperationalError as e:
        if 'duplicate column' in str(e).lower():
            logger.info("version column already exists")
        else:
            raise

    try:
        cursor.execute("ALTER TABLE legislation_digests ADD COLUMN active BOOLEAN DEFAULT 1")
        logger.info("Added active column")
    except sqlite3.OperationalError as e:
        if 'duplicate column' in str(e).lower():
            logger.info("active column already exists")
        else:
            raise

    # Create unique index: only one active digest per source
    try:
        cursor.execute("""
            CREATE UNIQUE INDEX idx_one_active_digest_per_source
            ON legislation_digests(legislation_source_id, active)
            WHERE active = 1
        """)
        logger.info("Created unique index for active digests")
    except sqlite3.OperationalError as e:
        if 'already exists' in str(e).lower():
            logger.info("Active digest index already exists")
        else:
            raise

    # ========================================
    # 2. Enhance rules table
    # ========================================
    logger.info("Adding lineage and modification tracking to rules")

    columns_to_add = [
        ('legislation_digest_id', 'INTEGER'),
        ('is_manually_modified', 'BOOLEAN DEFAULT 0'),
        ('original_rule_text', 'TEXT'),
        ('status', 'TEXT DEFAULT "active"'),
        ('supersedes_rule_id', 'INTEGER'),
    ]

    for column_name, column_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE rules ADD COLUMN {column_name} {column_type}")
            logger.info(f"Added {column_name} column to rules")
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e).lower():
                logger.info(f"{column_name} column already exists")
            else:
                raise

    # Create indexes
    try:
        cursor.execute("CREATE INDEX idx_rules_by_digest ON rules(legislation_digest_id)")
        logger.info("Created index on legislation_digest_id")
    except sqlite3.OperationalError as e:
        if 'already exists' in str(e).lower():
            logger.info("Index idx_rules_by_digest already exists")

    try:
        cursor.execute("CREATE INDEX idx_rules_status ON rules(status)")
        logger.info("Created index on status")
    except sqlite3.OperationalError as e:
        if 'already exists' in str(e).lower():
            logger.info("Index idx_rules_status already exists")

    # ========================================
    # 3. Populate digest_id for existing rules
    # ========================================
    logger.info("Populating digest_id for existing rules")

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
        AND legislation_digest_id IS NULL
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
        CREATE TABLE IF NOT EXISTS rule_collisions (
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
                REFERENCES rules(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_collisions_by_rule
        ON rule_collisions(rule_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_collisions_by_existing
        ON rule_collisions(collides_with_rule_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_collisions_pending
        ON rule_collisions(resolution)
        WHERE resolution IS NULL OR resolution = 'pending'
    """)

    logger.info("Created rule_collisions table and indexes")

    # ========================================
    # 5. Create llm_logs table
    # ========================================
    logger.info("Creating llm_logs table")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS llm_logs (
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes for common queries
    indexes = [
        ("idx_llm_logs_endpoint", "api_endpoint"),
        ("idx_llm_logs_operation", "operation_type"),
        ("idx_llm_logs_model", "model"),
        ("idx_llm_logs_created", "created_at"),
        ("idx_llm_logs_user", "user_id"),
        ("idx_llm_logs_cost", "total_cost_usd"),
        ("idx_llm_logs_status", "status"),
    ]

    for index_name, column_name in indexes:
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS {index_name}
            ON llm_logs({column_name})
        """)

    logger.info("Created llm_logs table and indexes")

    conn.commit()
    logger.info("Migration 008 completed successfully")


def discover_migrations_from_directory(migrations_dir: Path) -> List[Migration]:
    """
    Auto-discover migration files from a directory.

    Migration files must:
    - Be named like: 001_description.py, 002_description.py, etc.
    - Have an upgrade(conn) function
    - Optionally have a downgrade(conn) function

    Args:
        migrations_dir: Path to migrations directory

    Returns:
        List of discovered Migration objects
    """
    migrations = []

    if not migrations_dir.exists():
        logger.warning(f"Migrations directory not found: {migrations_dir}")
        return migrations

    # Find all .py files that match pattern: NNN_*.py
    migration_files = sorted(migrations_dir.glob("[0-9][0-9][0-9]_*.py"))

    for file_path in migration_files:
        try:
            # Extract version number from filename (e.g., "001" from "001_add_feature.py")
            filename = file_path.stem
            version_str = filename.split('_')[0]
            version = int(version_str)
            name = '_'.join(filename.split('_')[1:])  # Everything after version

            # Dynamically import the module
            spec = importlib.util.spec_from_file_location(f"migration_{version}", file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[f"migration_{version}"] = module
                spec.loader.exec_module(module)

                # Get upgrade and downgrade functions (try both naming conventions)
                upgrade_func = getattr(module, 'upgrade', None) or getattr(module, 'up', None)
                downgrade_func = getattr(module, 'downgrade', None) or getattr(module, 'down', None)

                if not upgrade_func:
                    logger.error(f"Migration {file_path.name} missing upgrade()/up() function, skipping")
                    continue

                migrations.append(Migration(version, name, upgrade_func, downgrade_func))
                logger.debug(f"Discovered migration: v{version} - {name}")

        except Exception as e:
            logger.error(f"Failed to load migration {file_path.name}: {e}")
            continue

    return migrations


def get_all_migrations() -> List[Migration]:
    """
    Get all migrations: both built-in (for backwards compat) and from files.

    Returns:
        Combined list of all migrations
    """
    # Built-in migrations (legacy, for backwards compatibility)
    builtin_migrations = [
        Migration(1, "add_base_url", migration_001_add_base_url),
        Migration(2, "add_screenshot_path", migration_002_add_screenshot_path),
        Migration(3, "add_deleted_at", migration_003_add_deleted_at),
        Migration(4, "add_token_tracking", migration_004_add_token_tracking),
        Migration(5, "add_visual_tokens", migration_005_add_visual_tokens),
        Migration(6, "add_llm_input_text", migration_006_add_llm_input_text),
        Migration(7, "create_llm_calls_table", migration_007_create_llm_calls_table),
        Migration(8, "add_versioning_and_logging", migration_008_add_versioning_and_logging),
    ]

    # Auto-discover migrations from /app/migrations directory (in Docker)
    migrations_dir = Path("/app/migrations")
    logger.info(f"Auto-discovering migrations from: {migrations_dir}")
    file_migrations = discover_migrations_from_directory(migrations_dir)
    logger.info(f"Discovered {len(file_migrations)} file-based migrations")

    # Combine and deduplicate (file migrations override builtin if version conflicts)
    all_migrations = {}

    # Add builtin first
    for m in builtin_migrations:
        all_migrations[m.version] = m

    # Override with file-based migrations
    for m in file_migrations:
        if m.version in all_migrations:
            logger.info(f"Migration v{m.version} from file overrides built-in version")
        all_migrations[m.version] = m

    # Return sorted by version
    return sorted(all_migrations.values(), key=lambda m: m.version)


def run_migrations(db_path: str):
    """
    Run all pending migrations (auto-discovers from files).

    Args:
        db_path: Path to SQLite database
    """
    migrations = get_all_migrations()
    runner = MigrationRunner(db_path)
    try:
        runner.run_migrations(migrations)
    finally:
        runner.close()


def get_migration_status(db_path: str) -> Dict:
    """
    Get migration status (auto-discovers from files).

    Args:
        db_path: Path to SQLite database

    Returns:
        Migration status dictionary
    """
    migrations = get_all_migrations()
    runner = MigrationRunner(db_path)
    try:
        return runner.get_status(migrations)
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
