#!/usr/bin/env python3
"""Management CLI for AutoAudit database operations."""

import sys
import argparse
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.migrations import run_migrations, get_migration_status, MIGRATIONS
from core.database import ComplianceDatabase
from core.config import DATABASE_PATH


def cmd_migrate(args):
    """Run pending database migrations."""
    print(f"Running migrations on {args.database}...")
    run_migrations(args.database)
    print("✓ Migrations complete")


def cmd_migration_status(args):
    """Show migration status."""
    status = get_migration_status(args.database)

    print(f"\n{'='*60}")
    print(f"  Migration Status")
    print(f"{'='*60}")
    print(f"Database: {args.database}")
    print(f"Applied:  {status['applied_count']} migrations")
    print(f"Pending:  {status['pending_count']} migrations")
    print(f"Latest:   v{status['latest_version']}")
    print(f"{'='*60}")

    if status['applied_versions']:
        print(f"\nApplied migrations:")
        for version in status['applied_versions']:
            migration = next((m for m in MIGRATIONS if m.version == version), None)
            if migration:
                print(f"  ✓ v{version}: {migration.name}")

    if status['pending_migrations']:
        print(f"\nPending migrations:")
        for m in status['pending_migrations']:
            print(f"  ⧗ v{m['version']}: {m['name']}")
    else:
        print(f"\n✓ All migrations up to date!")

    print()


def cmd_db_info(args):
    """Show database information."""
    db = ComplianceDatabase(args.database)
    try:
        # Get counts
        cursor = db.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM projects WHERE deleted_at IS NULL")
        projects_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM urls")
        urls_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM compliance_checks")
        checks_count = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(total_tokens) FROM compliance_checks")
        total_tokens = cursor.fetchone()[0] or 0

        print(f"\n{'='*60}")
        print(f"  Database Information")
        print(f"{'='*60}")
        print(f"Database:  {args.database}")
        print(f"Projects:  {projects_count}")
        print(f"URLs:      {urls_count}")
        print(f"Checks:    {checks_count}")
        print(f"Tokens:    {total_tokens:,}")
        print(f"{'='*60}\n")

    finally:
        db.close()


def cmd_create_user(args):
    """Create a new user."""
    from getpass import getpass
    import bcrypt

    db = ComplianceDatabase(args.database)
    try:
        # Check if user exists
        existing = db.get_user(email=args.email)
        if existing:
            print(f"Error: User with email '{args.email}' already exists")
            sys.exit(1)

        # Get password
        if args.password:
            password = args.password
        else:
            password = getpass("Password: ")
            password_confirm = getpass("Confirm password: ")
            if password != password_confirm:
                print("Error: Passwords do not match")
                sys.exit(1)

        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Create user
        user_id = db.create_user(
            email=args.email,
            password_hash=password_hash,
            full_name=args.name
        )

        print(f"✓ User created successfully")
        print(f"  ID: {user_id}")
        print(f"  Email: {args.email}")
        print(f"  Name: {args.name or '(none)'}")

    finally:
        db.close()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AutoAudit Database Management",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--database',
        default=DATABASE_PATH,
        help=f'Database path (default: {DATABASE_PATH})'
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Run pending migrations')
    migrate_parser.set_defaults(func=cmd_migrate)

    # migration:status command
    status_parser = subparsers.add_parser('migration:status', help='Show migration status')
    status_parser.set_defaults(func=cmd_migration_status)

    # db:info command
    info_parser = subparsers.add_parser('db:info', help='Show database information')
    info_parser.set_defaults(func=cmd_db_info)

    # user:create command
    user_parser = subparsers.add_parser('user:create', help='Create a new user')
    user_parser.add_argument('email', help='User email address')
    user_parser.add_argument('--name', help='User full name')
    user_parser.add_argument('--password', help='User password (will prompt if not provided)')
    user_parser.set_defaults(func=cmd_create_user)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == '__main__':
    main()
