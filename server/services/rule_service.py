"""Rule management service."""

from typing import List, Optional
from datetime import datetime
import logging

from core.database import ComplianceDatabase
from schemas.rule import (
    RuleCreate, RuleUpdate, RuleResponse
)

logger = logging.getLogger(__name__)


class RuleService:
    """Service for managing compliance rules."""

    def __init__(self, db: ComplianceDatabase):
        """Initialize service with database."""
        self.db = db

    def create_rule(self, rule_data: RuleCreate) -> RuleResponse:
        """Create a new rule."""
        conn = self.db.conn
        cursor = conn.cursor()

        try:
            # Store original text if this is AI-generated
            original_text = rule_data.rule_text if rule_data.legislation_digest_id else None

            cursor.execute("""
                INSERT INTO rules (
                    state_code, legislation_source_id, legislation_digest_id,
                    rule_text, applies_to_page_types, active, approved,
                    is_manually_modified, original_rule_text, status, supersedes_rule_id,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule_data.state_code.upper(),
                rule_data.legislation_source_id,
                rule_data.legislation_digest_id,
                rule_data.rule_text,
                rule_data.applies_to_page_types,
                rule_data.active,
                rule_data.approved,
                rule_data.is_manually_modified,
                original_text,
                rule_data.status,
                rule_data.supersedes_rule_id,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            conn.commit()
            rule_id = cursor.lastrowid
            logger.info(f"Created rule: {rule_id}")
            return self.get_rule(rule_id)
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to create rule: {e}")
            raise ValueError(f"Failed to create rule: {str(e)}")

    def get_rule(self, rule_id: int) -> Optional[RuleResponse]:
        """Get a rule by ID."""
        conn = self.db.conn
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, state_code, legislation_source_id, legislation_digest_id,
                   rule_text, applies_to_page_types, active, approved,
                   is_manually_modified, original_rule_text, status, supersedes_rule_id,
                   created_at, updated_at
            FROM rules
            WHERE id = ?
        """, (rule_id,))

        row = cursor.fetchone()

        if row:
            return self._row_to_rule(row)
        return None

    def list_rules(
        self,
        state_code: Optional[str] = None,
        active_only: bool = False,
        approved_only: bool = False
    ) -> List[RuleResponse]:
        """List rules with optional filters."""
        conn = self.db.conn
        cursor = conn.cursor()

        query = """
            SELECT id, state_code, legislation_source_id, legislation_digest_id,
                   rule_text, applies_to_page_types, active, approved,
                   is_manually_modified, original_rule_text, status, supersedes_rule_id,
                   created_at, updated_at
            FROM rules
        """

        conditions = []
        params = []

        if state_code:
            conditions.append("state_code = ?")
            params.append(state_code.upper())

        if active_only:
            conditions.append("active = 1")

        if approved_only:
            conditions.append("approved = 1")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY state_code, created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [self._row_to_rule(row) for row in rows]

    def update_rule(self, rule_id: int, rule_data: RuleUpdate) -> RuleResponse:
        """Update a rule."""
        conn = self.db.conn
        cursor = conn.cursor()

        try:
            updates = []
            values = []

            # If rule_text is being modified, set is_manually_modified flag
            if rule_data.rule_text is not None:
                # Get the current rule to check if text is actually changing
                current_rule = self.get_rule(rule_id)
                if current_rule and current_rule.rule_text != rule_data.rule_text:
                    # Text is changing - mark as manually modified
                    updates.append("is_manually_modified = ?")
                    values.append(True)
                updates.append("rule_text = ?")
                values.append(rule_data.rule_text)

            # Handle all updateable fields
            if rule_data.state_code is not None:
                updates.append("state_code = ?")
                values.append(rule_data.state_code.upper())

            if rule_data.legislation_source_id is not None:
                updates.append("legislation_source_id = ?")
                values.append(rule_data.legislation_source_id)

            if rule_data.legislation_digest_id is not None:
                updates.append("legislation_digest_id = ?")
                values.append(rule_data.legislation_digest_id)

            if rule_data.applies_to_page_types is not None:
                updates.append("applies_to_page_types = ?")
                values.append(rule_data.applies_to_page_types)

            if rule_data.active is not None:
                updates.append("active = ?")
                values.append(rule_data.active)

            if rule_data.approved is not None:
                updates.append("approved = ?")
                values.append(rule_data.approved)

            if rule_data.original_rule_text is not None:
                updates.append("original_rule_text = ?")
                values.append(rule_data.original_rule_text)

            if rule_data.status is not None:
                updates.append("status = ?")
                values.append(rule_data.status)

            if rule_data.supersedes_rule_id is not None:
                updates.append("supersedes_rule_id = ?")
                values.append(rule_data.supersedes_rule_id)

            # Allow explicit setting of is_manually_modified
            if rule_data.is_manually_modified is not None:
                # Only add if not already added above
                if "is_manually_modified = ?" not in updates:
                    updates.append("is_manually_modified = ?")
                    values.append(rule_data.is_manually_modified)

            if not updates:
                return self.get_rule(rule_id)

            updates.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(rule_id)

            cursor.execute(f"""
                UPDATE rules
                SET {', '.join(updates)}
                WHERE id = ?
            """, values)

            conn.commit()
            logger.info(f"Updated rule {rule_id}")
            return self.get_rule(rule_id)
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to update rule: {e}")
            raise ValueError(f"Failed to update rule: {str(e)}")

    def delete_rule(self, rule_id: int) -> None:
        """Delete a rule."""
        conn = self.db.conn
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
            conn.commit()
            logger.info(f"Deleted rule {rule_id}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to delete rule: {e}")
            raise ValueError(f"Failed to delete rule: {str(e)}")

    def delete_rules_by_legislation_source(self, source_id: int) -> int:
        """
        Delete ALL rules associated with a legislation source.

        This is used when the entire legislation source is being deleted.
        All rules are deleted regardless of approval or modification status.

        Returns count of rules deleted.
        """
        conn = self.db.conn
        cursor = conn.cursor()

        try:
            # Get count before deletion
            cursor.execute(
                "SELECT COUNT(*) FROM rules WHERE legislation_source_id = ?",
                (source_id,)
            )
            count = cursor.fetchone()[0]

            # Delete ALL rules
            cursor.execute(
                "DELETE FROM rules WHERE legislation_source_id = ?",
                (source_id,)
            )
            conn.commit()
            logger.info(f"Deleted {count} rules for legislation source {source_id}")
            return count
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to delete rules by source: {e}")
            raise ValueError(f"Failed to delete rules by source: {str(e)}")

    def delete_rules_by_digest(self, digest_id: int) -> dict:
        """
        Delete rules associated with a specific digest when re-digesting.

        IMPORTANT: Only deletes rules that are NOT approved AND NOT manually modified.
        Approved or manually edited rules are preserved WITH their digest_id intact
        to maintain full lineage trail.

        Protection is determined by the approved/is_manually_modified flags,
        NOT by removing the digest link.

        This is used when re-digesting legislation - we want to preserve user work.

        Returns dict with deleted and protected counts.
        """
        conn = self.db.conn
        cursor = conn.cursor()

        try:
            # Count deletable rules (not approved, not manually modified)
            cursor.execute("""
                SELECT COUNT(*)
                FROM rules
                WHERE legislation_digest_id = ?
                AND approved = 0
                AND is_manually_modified = 0
            """, (digest_id,))
            deleted_count = cursor.fetchone()[0]

            # Count protected rules (will NOT be deleted)
            cursor.execute("""
                SELECT COUNT(*)
                FROM rules
                WHERE legislation_digest_id = ?
                AND (approved = 1 OR is_manually_modified = 1)
            """, (digest_id,))
            protected_count = cursor.fetchone()[0]

            # Delete only unapproved, unmodified rules
            # Protected rules keep their digest_id for full lineage trail
            cursor.execute("""
                DELETE FROM rules
                WHERE legislation_digest_id = ?
                AND approved = 0
                AND is_manually_modified = 0
            """, (digest_id,))

            conn.commit()

            logger.info(
                f"Digest {digest_id}: Deleted {deleted_count} unapproved rules, "
                f"preserved {protected_count} approved/modified rules (kept digest lineage)"
            )

            return {
                "deleted": deleted_count,
                "protected": protected_count
            }

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to delete rules by digest: {e}")
            raise ValueError(f"Failed to delete rules by digest: {str(e)}")

    def get_protected_rules_count(self, digest_id: int) -> int:
        """
        Get count of protected rules (approved OR manually modified) for a digest.
        These rules will NOT be deleted when re-digesting.
        """
        conn = self.db.conn
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM rules
            WHERE legislation_digest_id = ?
            AND (approved = 1 OR is_manually_modified = 1)
        """, (digest_id,))

        return cursor.fetchone()[0]

    def delete_rules_by_state(self, state_code: str) -> int:
        """
        Delete all rules for a state.
        Returns count of rules deleted.
        """
        conn = self.db.conn
        cursor = conn.cursor()

        try:
            # Get count before deletion
            cursor.execute(
                "SELECT COUNT(*) FROM rules WHERE state_code = ?",
                (state_code.upper(),)
            )
            count = cursor.fetchone()[0]

            # Delete rules
            cursor.execute(
                "DELETE FROM rules WHERE state_code = ?",
                (state_code.upper(),)
            )
            conn.commit()
            logger.info(f"Deleted {count} rules for state {state_code}")
            return count
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to delete rules by state: {e}")
            raise ValueError(f"Failed to delete rules by state: {str(e)}")

    def _row_to_rule(self, row) -> RuleResponse:
        """Convert database row to RuleResponse."""
        return RuleResponse(
            id=row[0],
            state_code=row[1],
            legislation_source_id=row[2],
            legislation_digest_id=row[3],
            rule_text=row[4],
            applies_to_page_types=row[5],
            active=bool(row[6]),
            approved=bool(row[7]),
            is_manually_modified=bool(row[8]),
            original_rule_text=row[9],
            status=row[10],
            supersedes_rule_id=row[11],
            created_at=datetime.fromisoformat(row[12]),
            updated_at=datetime.fromisoformat(row[13])
        )
