"""API routes for demo and testing utilities."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict
import logging
import os

from core.database import ComplianceDatabase
from api.dependencies import get_db, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["demo"])

# Check if we're in production
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"


def check_not_production():
    """Raise error if in production environment."""
    if IS_PRODUCTION:
        raise HTTPException(
            status_code=403,
            detail="Demo utilities are disabled in production for safety"
        )


@router.delete("/rules", response_model=Dict)
async def clear_all_rules(
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Clear all compliance rules.
    WARNING: This is destructive and cannot be undone.
    DISABLED IN PRODUCTION.
    """
    check_not_production()
    cursor = db.conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM rules")
        count = cursor.fetchone()[0]

        cursor.execute("DELETE FROM rules")
        db.conn.commit()

        logger.warning(f"User {current_user.get('email')} deleted {count} rules")

        return {
            "message": f"Deleted {count} rules",
            "deleted_count": count
        }
    except Exception as e:
        db.conn.rollback()
        logger.error(f"Failed to clear rules: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear rules: {str(e)}")


@router.delete("/preambles", response_model=Dict)
async def clear_all_preambles(
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Clear all preambles and their versions.
    WARNING: This is destructive and cannot be undone.
    DISABLED IN PRODUCTION.
    """
    check_not_production()
    cursor = db.conn.cursor()

    try:
        # Count before deletion
        cursor.execute("SELECT COUNT(*) FROM preambles")
        preambles_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM preamble_versions")
        versions_count = cursor.fetchone()[0]

        # Delete (cascade will handle versions and related data)
        cursor.execute("DELETE FROM preamble_test_runs")
        cursor.execute("DELETE FROM preamble_version_performance")
        cursor.execute("DELETE FROM project_page_type_preambles")
        cursor.execute("DELETE FROM default_page_type_preambles")
        cursor.execute("DELETE FROM preamble_versions")
        cursor.execute("DELETE FROM preambles")
        db.conn.commit()

        logger.warning(f"User {current_user.get('email')} deleted {preambles_count} preambles and {versions_count} versions")

        return {
            "message": f"Deleted {preambles_count} preambles and {versions_count} versions",
            "preambles_deleted": preambles_count,
            "versions_deleted": versions_count
        }
    except Exception as e:
        db.conn.rollback()
        logger.error(f"Failed to clear preambles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear preambles: {str(e)}")


@router.delete("/projects", response_model=Dict)
async def clear_all_projects(
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Clear all projects and associated data (URLs, checks, etc.).
    WARNING: This is destructive and cannot be undone.
    DISABLED IN PRODUCTION.
    """
    check_not_production()
    cursor = db.conn.cursor()

    try:
        # Count before deletion
        cursor.execute("SELECT COUNT(*) FROM projects")
        projects_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM urls")
        urls_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM compliance_checks")
        checks_count = cursor.fetchone()[0]

        # Delete in order (respecting foreign keys)
        cursor.execute("DELETE FROM compliance_checks")
        cursor.execute("DELETE FROM urls")
        cursor.execute("DELETE FROM project_page_type_preambles")
        cursor.execute("DELETE FROM projects")
        db.conn.commit()

        logger.warning(f"User {current_user.get('email')} deleted {projects_count} projects, {urls_count} URLs, {checks_count} checks")

        return {
            "message": f"Deleted {projects_count} projects, {urls_count} URLs, and {checks_count} checks",
            "projects_deleted": projects_count,
            "urls_deleted": urls_count,
            "checks_deleted": checks_count
        }
    except Exception as e:
        db.conn.rollback()
        logger.error(f"Failed to clear projects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear projects: {str(e)}")


@router.delete("/users", response_model=Dict)
async def clear_all_users_except_current(
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Clear all users EXCEPT the currently logged in user.
    WARNING: This is destructive and cannot be undone.
    DISABLED IN PRODUCTION.
    """
    check_not_production()
    cursor = db.conn.cursor()

    try:
        current_user_id = current_user.get('id')

        cursor.execute("SELECT COUNT(*) FROM users WHERE id != ?", (current_user_id,))
        count = cursor.fetchone()[0]

        # Delete refresh tokens first (foreign key)
        cursor.execute("DELETE FROM refresh_tokens WHERE user_id != ?", (current_user_id,))

        # Delete users
        cursor.execute("DELETE FROM users WHERE id != ?", (current_user_id,))
        db.conn.commit()

        logger.warning(f"User {current_user.get('email')} deleted {count} other users")

        return {
            "message": f"Deleted {count} users (kept current user: {current_user.get('email')})",
            "deleted_count": count,
            "kept_user": current_user.get('email')
        }
    except Exception as e:
        db.conn.rollback()
        logger.error(f"Failed to clear users: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear users: {str(e)}")


@router.delete("/legislation", response_model=Dict)
async def clear_all_legislation(
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Clear all legislation sources and digests.
    WARNING: This is destructive and cannot be undone.
    DISABLED IN PRODUCTION.
    """
    check_not_production()
    cursor = db.conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM legislation_sources")
        sources_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM legislation_digests")
        digests_count = cursor.fetchone()[0]

        # Delete (cascade should handle digests)
        cursor.execute("DELETE FROM legislation_digests")
        cursor.execute("DELETE FROM legislation_sources")
        db.conn.commit()

        logger.warning(f"User {current_user.get('email')} deleted {sources_count} legislation sources and {digests_count} digests")

        return {
            "message": f"Deleted {sources_count} legislation sources and {digests_count} digests",
            "sources_deleted": sources_count,
            "digests_deleted": digests_count
        }
    except Exception as e:
        db.conn.rollback()
        logger.error(f"Failed to clear legislation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear legislation: {str(e)}")


@router.delete("/everything", response_model=Dict)
async def reset_to_clean_slate(
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    NUCLEAR OPTION: Clear ALL data except states, page types, and current user.
    This resets the system to a clean slate for demos.
    WARNING: This is EXTREMELY destructive and cannot be undone.
    DISABLED IN PRODUCTION.
    """
    check_not_production()
    cursor = db.conn.cursor()

    try:
        current_user_id = current_user.get('id')

        # Count everything before deletion
        counts = {}
        tables = [
            "compliance_checks", "urls", "projects",
            "rules", "legislation_digests", "legislation_sources",
            "preamble_test_runs", "preamble_version_performance",
            "project_page_type_preambles", "default_page_type_preambles",
            "preamble_versions", "preambles"
        ]

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cursor.fetchone()[0]

        # Delete in order (respecting foreign keys)
        cursor.execute("DELETE FROM compliance_checks")
        cursor.execute("DELETE FROM urls")
        cursor.execute("DELETE FROM project_page_type_preambles")
        cursor.execute("DELETE FROM projects")
        cursor.execute("DELETE FROM rules")
        cursor.execute("DELETE FROM legislation_digests")
        cursor.execute("DELETE FROM legislation_sources")
        cursor.execute("DELETE FROM preamble_test_runs")
        cursor.execute("DELETE FROM preamble_version_performance")
        cursor.execute("DELETE FROM default_page_type_preambles")
        cursor.execute("DELETE FROM preamble_versions")
        cursor.execute("DELETE FROM preambles")

        # Delete other users (keep current user)
        cursor.execute("DELETE FROM refresh_tokens WHERE user_id != ?", (current_user_id,))
        cursor.execute("SELECT COUNT(*) FROM users WHERE id != ?", (current_user_id,))
        other_users_count = cursor.fetchone()[0]
        cursor.execute("DELETE FROM users WHERE id != ?", (current_user_id,))

        db.conn.commit()

        total_deleted = sum(counts.values()) + other_users_count

        logger.warning(f"User {current_user.get('email')} performed NUCLEAR RESET - deleted {total_deleted} records")

        return {
            "message": f"✨ System reset to clean slate. Deleted {total_deleted} total records.",
            "details": {
                **counts,
                "other_users": other_users_count
            },
            "kept": {
                "user": current_user.get('email'),
                "states": "preserved",
                "page_types": "preserved"
            }
        }
    except Exception as e:
        db.conn.rollback()
        logger.error(f"Failed to reset system: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset system: {str(e)}")
