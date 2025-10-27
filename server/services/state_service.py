"""State and legislation management service."""

from typing import List, Optional, Dict
from datetime import datetime
import logging

from core.database import ComplianceDatabase
from schemas.state import (
    StateCreate, StateUpdate, StateResponse,
    LegislationSourceCreate, LegislationSourceUpdate, LegislationSourceResponse,
    LegislationDigestCreate, LegislationDigestUpdate, LegislationDigestResponse
)

logger = logging.getLogger(__name__)


class StateService:
    """Service for managing states and legislation."""

    def __init__(self, db: ComplianceDatabase):
        """Initialize service with database."""
        self.db = db

    # States
    def create_state(self, state_data: StateCreate) -> StateResponse:
        """Create a new state."""
        conn = self.db.conn
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO states (code, name, active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                state_data.code.upper(),
                state_data.name,
                state_data.active,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            conn.commit()
            state_id = cursor.lastrowid
            logger.info(f"Created state: {state_data.code}")
            return self.get_state(state_id)
        except Exception as e:
            conn.rollback()
            raise ValueError(f"Failed to create state: {str(e)}")

    def get_state(self, state_id: int) -> Optional[StateResponse]:
        """Get a state by ID."""
        conn = self.db.conn
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, code, name, active, created_at, updated_at
            FROM states
            WHERE id = ?
        """, (state_id,))

        row = cursor.fetchone()

        if row:
            return StateResponse(
                id=row[0],
                code=row[1],
                name=row[2],
                active=bool(row[3]),
                created_at=datetime.fromisoformat(row[4]),
                updated_at=datetime.fromisoformat(row[5])
            )
        return None

    def get_state_by_code(self, state_code: str) -> Optional[StateResponse]:
        """Get a state by code."""
        conn = self.db.conn
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, code, name, active, created_at, updated_at
            FROM states
            WHERE code = ?
        """, (state_code.upper(),))

        row = cursor.fetchone()

        if row:
            return StateResponse(
                id=row[0],
                code=row[1],
                name=row[2],
                active=bool(row[3]),
                created_at=datetime.fromisoformat(row[4]),
                updated_at=datetime.fromisoformat(row[5])
            )
        return None

    def list_states(self, active_only: bool = False) -> List[StateResponse]:
        """List all states."""
        conn = self.db.conn
        cursor = conn.cursor()

        query = "SELECT id, code, name, active, created_at, updated_at FROM states"
        if active_only:
            query += " WHERE active = 1"
        query += " ORDER BY name"

        cursor.execute(query)
        rows = cursor.fetchall()

        return [
            StateResponse(
                id=row[0],
                code=row[1],
                name=row[2],
                active=bool(row[3]),
                created_at=datetime.fromisoformat(row[4]),
                updated_at=datetime.fromisoformat(row[5])
            )
            for row in rows
        ]

    def update_state(self, state_id: int, state_data: StateUpdate) -> StateResponse:
        """Update a state."""
        conn = self.db.conn
        cursor = conn.cursor()

        try:
            updates = []
            values = []

            if state_data.name is not None:
                updates.append("name = ?")
                values.append(state_data.name)

            if state_data.active is not None:
                updates.append("active = ?")
                values.append(state_data.active)

            if not updates:
                return self.get_state(state_id)

            updates.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(state_id)

            cursor.execute(f"""
                UPDATE states
                SET {', '.join(updates)}
                WHERE id = ?
            """, values)

            conn.commit()
            logger.info(f"Updated state {state_id}")
            return self.get_state(state_id)
        except Exception as e:
            conn.rollback()
            raise ValueError(f"Failed to update state: {str(e)}")

    # Legislation Sources
    def create_legislation_source(
        self,
        source_data: LegislationSourceCreate
    ) -> LegislationSourceResponse:
        """Create a new legislation source."""
        conn = self.db.conn
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO legislation_sources (
                    state_code, statute_number, title, full_text, source_url,
                    effective_date, sunset_date, last_verified_date,
                    applies_to_page_types, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source_data.state_code.upper(),
                source_data.statute_number,
                source_data.title,
                source_data.full_text,
                source_data.source_url,
                source_data.effective_date.isoformat() if source_data.effective_date else None,
                source_data.sunset_date.isoformat() if source_data.sunset_date else None,
                source_data.last_verified_date.isoformat() if source_data.last_verified_date else None,
                source_data.applies_to_page_types,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            conn.commit()
            source_id = cursor.lastrowid
            logger.info(f"Created legislation source: {source_data.statute_number}")
            return self.get_legislation_source(source_id)
        except Exception as e:
            conn.rollback()
            raise ValueError(f"Failed to create legislation source: {str(e)}")

    def get_legislation_source(self, source_id: int) -> Optional[LegislationSourceResponse]:
        """Get a legislation source by ID."""
        conn = self.db.conn
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, state_code, statute_number, title, full_text, source_url,
                   effective_date, sunset_date, last_verified_date,
                   applies_to_page_types, created_at, updated_at
            FROM legislation_sources
            WHERE id = ?
        """, (source_id,))

        row = cursor.fetchone()

        if row:
            return self._row_to_legislation_source(row)
        return None

    def list_legislation_sources(
        self,
        state_code: Optional[str] = None
    ) -> List[LegislationSourceResponse]:
        """List legislation sources, optionally filtered by state."""
        conn = self.db.conn
        cursor = conn.cursor()

        query = """
            SELECT id, state_code, statute_number, title, full_text, source_url,
                   effective_date, sunset_date, last_verified_date,
                   applies_to_page_types, created_at, updated_at
            FROM legislation_sources
        """

        if state_code:
            query += " WHERE state_code = ?"
            cursor.execute(query + " ORDER BY statute_number", (state_code.upper(),))
        else:
            cursor.execute(query + " ORDER BY state_code, statute_number")

        rows = cursor.fetchall()

        return [self._row_to_legislation_source(row) for row in rows]

    def update_legislation_source(
        self,
        source_id: int,
        source_data: LegislationSourceUpdate
    ) -> LegislationSourceResponse:
        """Update a legislation source."""
        conn = self.db.conn
        cursor = conn.cursor()

        try:
            updates = []
            values = []

            fields = [
                ('statute_number', source_data.statute_number),
                ('title', source_data.title),
                ('full_text', source_data.full_text),
                ('source_url', source_data.source_url),
                ('applies_to_page_types', source_data.applies_to_page_types)
            ]

            for field_name, field_value in fields:
                if field_value is not None:
                    updates.append(f"{field_name} = ?")
                    values.append(field_value)

            # Date fields
            if source_data.effective_date is not None:
                updates.append("effective_date = ?")
                values.append(source_data.effective_date.isoformat())

            if source_data.sunset_date is not None:
                updates.append("sunset_date = ?")
                values.append(source_data.sunset_date.isoformat())

            if source_data.last_verified_date is not None:
                updates.append("last_verified_date = ?")
                values.append(source_data.last_verified_date.isoformat())

            if not updates:
                return self.get_legislation_source(source_id)

            updates.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(source_id)

            cursor.execute(f"""
                UPDATE legislation_sources
                SET {', '.join(updates)}
                WHERE id = ?
            """, values)

            conn.commit()
            logger.info(f"Updated legislation source {source_id}")
            return self.get_legislation_source(source_id)
        except Exception as e:
            conn.rollback()
            raise ValueError(f"Failed to update legislation source: {str(e)}")

    def delete_legislation_source(self, source_id: int) -> Dict:
        """
        Delete a legislation source and all associated data.

        This will cascade delete:
        - All legislation digests for this source
        - All compliance rules generated from this source (handled by DB ON DELETE CASCADE)

        Returns a dict with counts of deleted items.
        """
        conn = self.db.conn
        cursor = conn.cursor()

        try:
            # Check if source exists
            source = self.get_legislation_source(source_id)
            if not source:
                raise ValueError(f"Legislation source {source_id} not found")

            # Count what will be deleted
            cursor.execute("SELECT COUNT(*) FROM legislation_digests WHERE legislation_source_id = ?", (source_id,))
            digest_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM rules WHERE legislation_source_id = ?", (source_id,))
            rule_count = cursor.fetchone()[0]

            # Delete legislation digests (not cascade in DB, so we do it manually)
            cursor.execute("DELETE FROM legislation_digests WHERE legislation_source_id = ?", (source_id,))

            # Delete the legislation source (rules will cascade delete due to ON DELETE CASCADE)
            cursor.execute("DELETE FROM legislation_sources WHERE id = ?", (source_id,))

            conn.commit()

            logger.info(f"Deleted legislation source {source_id}: {digest_count} digests, {rule_count} rules")

            return {
                "legislation_source_id": source_id,
                "statute_number": source.statute_number,
                "digests_deleted": digest_count,
                "rules_deleted": rule_count
            }

        except ValueError:
            # Re-raise ValueError (not found) without rollback
            raise
        except Exception as e:
            conn.rollback()
            raise ValueError(f"Failed to delete legislation source: {str(e)}")

    # Legislation Digests
    def create_legislation_digest(
        self,
        digest_data: LegislationDigestCreate
    ) -> LegislationDigestResponse:
        """Create a new legislation digest."""
        conn = self.db.conn
        cursor = conn.cursor()

        try:
            # Get the next version number for this legislation source
            cursor.execute("""
                SELECT COALESCE(MAX(version), 0) + 1
                FROM legislation_digests
                WHERE legislation_source_id = ?
            """, (digest_data.legislation_source_id,))
            next_version = cursor.fetchone()[0]

            # Deactivate any existing active digest for this source
            cursor.execute("""
                UPDATE legislation_digests
                SET active = 0
                WHERE legislation_source_id = ? AND active = 1
            """, (digest_data.legislation_source_id,))

            cursor.execute("""
                INSERT INTO legislation_digests (
                    legislation_source_id, version, active,
                    interpreted_requirements, created_by, approved,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                digest_data.legislation_source_id,
                next_version,
                1,  # New digest is active
                digest_data.interpreted_requirements,
                digest_data.created_by,
                digest_data.approved,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            conn.commit()
            digest_id = cursor.lastrowid
            logger.info(f"Created legislation digest {digest_id} (version {next_version})")
            return self.get_legislation_digest(digest_id)
        except Exception as e:
            conn.rollback()
            raise ValueError(f"Failed to create legislation digest: {str(e)}")

    def get_legislation_digest(self, digest_id: int) -> Optional[LegislationDigestResponse]:
        """Get a legislation digest by ID."""
        conn = self.db.conn
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, legislation_source_id, version, active,
                   interpreted_requirements, created_by, reviewed_by,
                   last_review_date, approved, created_at, updated_at
            FROM legislation_digests
            WHERE id = ?
        """, (digest_id,))

        row = cursor.fetchone()

        if row:
            return self._row_to_legislation_digest(row)
        return None

    def list_legislation_digests(
        self,
        legislation_source_id: Optional[int] = None,
        approved_only: bool = False
    ) -> List[LegislationDigestResponse]:
        """List legislation digests."""
        conn = self.db.conn
        cursor = conn.cursor()

        query = """
            SELECT id, legislation_source_id, version, active,
                   interpreted_requirements, created_by, reviewed_by,
                   last_review_date, approved, created_at, updated_at
            FROM legislation_digests
        """

        conditions = []
        params = []

        if legislation_source_id:
            conditions.append("legislation_source_id = ?")
            params.append(legislation_source_id)

        if approved_only:
            conditions.append("approved = 1")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY version DESC, created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [self._row_to_legislation_digest(row) for row in rows]

    def update_legislation_digest(
        self,
        digest_id: int,
        digest_data: LegislationDigestUpdate
    ) -> LegislationDigestResponse:
        """Update a legislation digest."""
        conn = self.db.conn
        cursor = conn.cursor()

        try:
            updates = []
            values = []

            if digest_data.interpreted_requirements is not None:
                updates.append("interpreted_requirements = ?")
                values.append(digest_data.interpreted_requirements)

            if digest_data.approved is not None:
                updates.append("approved = ?")
                values.append(digest_data.approved)

            if digest_data.reviewed_by is not None:
                updates.append("reviewed_by = ?")
                values.append(digest_data.reviewed_by)
                updates.append("last_review_date = ?")
                values.append(datetime.now().isoformat())

            if not updates:
                return self.get_legislation_digest(digest_id)

            updates.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(digest_id)

            cursor.execute(f"""
                UPDATE legislation_digests
                SET {', '.join(updates)}
                WHERE id = ?
            """, values)

            conn.commit()
            logger.info(f"Updated legislation digest {digest_id}")
            return self.get_legislation_digest(digest_id)
        except Exception as e:
            conn.rollback()
            raise ValueError(f"Failed to update legislation digest: {str(e)}")

    # Helper methods
    def _row_to_legislation_source(self, row) -> LegislationSourceResponse:
        """Convert database row to LegislationSourceResponse."""
        from datetime import date as date_type

        return LegislationSourceResponse(
            id=row[0],
            state_code=row[1],
            statute_number=row[2],
            title=row[3],
            full_text=row[4],
            source_url=row[5],
            effective_date=date_type.fromisoformat(row[6]) if row[6] else None,
            sunset_date=date_type.fromisoformat(row[7]) if row[7] else None,
            last_verified_date=date_type.fromisoformat(row[8]) if row[8] else None,
            applies_to_page_types=row[9],
            created_at=datetime.fromisoformat(row[10]),
            updated_at=datetime.fromisoformat(row[11])
        )

    def _row_to_legislation_digest(self, row) -> LegislationDigestResponse:
        """Convert database row to LegislationDigestResponse."""
        return LegislationDigestResponse(
            id=row[0],
            legislation_source_id=row[1],
            interpreted_requirements=row[4],
            created_by=row[5],
            reviewed_by=row[6],
            last_review_date=datetime.fromisoformat(row[7]) if row[7] else None,
            approved=bool(row[8]),
            created_at=datetime.fromisoformat(row[9]),
            updated_at=datetime.fromisoformat(row[10])
        )
