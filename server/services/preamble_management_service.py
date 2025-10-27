"""Preamble management service for CRUD operations on preambles and versions."""

from typing import List, Optional, Dict
from datetime import datetime
import logging
import re

from core.database import ComplianceDatabase
from schemas.preamble import (
    PreambleCreate, PreambleResponse,
    PreambleVersionCreate, PreambleVersionUpdate, PreambleVersionResponse,
    PreambleTemplateCreate, PreambleTemplateResponse,
    DefaultPageTypePreambleCreate, DefaultPageTypePreambleResponse,
    ProjectPageTypePreambleCreate, ProjectPageTypePreambleResponse,
    PreambleTestRunCreate, PreambleTestRunResponse,
    PreambleVersionPerformanceResponse
)
from services.preamble_service import PreambleService

logger = logging.getLogger(__name__)


class PreambleManagementService:
    """Service for managing preambles, versions, and templates."""

    def __init__(self, db: ComplianceDatabase):
        """Initialize service with database."""
        self.db = db
        self.composition_service = PreambleService(db)

    # Preamble Templates
    def create_template(self, template_data: PreambleTemplateCreate) -> PreambleTemplateResponse:
        """Create a new preamble template."""
        conn = self.db.conn
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO preamble_templates (name, description, template_structure, is_default, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                template_data.name,
                template_data.description,
                template_data.template_structure,
                template_data.is_default,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            conn.commit()
            template_id = cursor.lastrowid
            logger.info(f"Created preamble template: {template_data.name}")
            return self.get_template(template_id)
        except Exception as e:
            conn.rollback()
            raise ValueError(f"Failed to create template: {str(e)}")
        finally:
            conn.close()

    def get_template(self, template_id: int) -> Optional[PreambleTemplateResponse]:
        """Get a preamble template by ID."""
        conn = self.db.conn
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, description, template_structure, is_default, created_at, updated_at
            FROM preamble_templates
            WHERE id = ?
        """, (template_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return PreambleTemplateResponse(
                id=row[0],
                name=row[1],
                description=row[2],
                template_structure=row[3],
                is_default=bool(row[4]),
                created_at=datetime.fromisoformat(row[5]),
                updated_at=datetime.fromisoformat(row[6])
            )
        return None

    def list_templates(self) -> List[PreambleTemplateResponse]:
        """List all preamble templates."""
        conn = self.db.conn
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, description, template_structure, is_default, created_at, updated_at
            FROM preamble_templates
            ORDER BY is_default DESC, name
        """)

        rows = cursor.fetchall()
        conn.close()

        return [
            PreambleTemplateResponse(
                id=row[0],
                name=row[1],
                description=row[2],
                template_structure=row[3],
                is_default=bool(row[4]),
                created_at=datetime.fromisoformat(row[5]),
                updated_at=datetime.fromisoformat(row[6])
            )
            for row in rows
        ]

    # Preambles
    def create_preamble(self, preamble_data: PreambleCreate) -> PreambleResponse:
        """Create a new preamble with initial version."""
        conn = self.db.conn
        cursor = conn.cursor()

        try:
            # Generate machine name
            machine_name = self._generate_machine_name(
                scope=preamble_data.scope,
                state_code=preamble_data.state_code,
                page_type_code=preamble_data.page_type_code,
                project_id=preamble_data.project_id,
                created_via=preamble_data.created_via
            )

            # Insert preamble
            cursor.execute("""
                INSERT INTO preambles (
                    name, machine_name, scope, page_type_code, state_code,
                    project_id, created_via, created_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                preamble_data.name,
                machine_name,
                preamble_data.scope,
                preamble_data.page_type_code,
                preamble_data.state_code.upper() if preamble_data.state_code else None,
                preamble_data.project_id,
                preamble_data.created_via,
                datetime.now().isoformat(),
                preamble_data.created_by
            ))

            preamble_id = cursor.lastrowid

            # Create initial version (always active)
            cursor.execute("""
                INSERT INTO preamble_versions (
                    preamble_id, version_number, preamble_text, change_summary,
                    status, created_at, created_by
                ) VALUES (?, 1, ?, ?, 'active', ?, ?)
            """, (
                preamble_id,
                preamble_data.initial_text,
                "Initial version",
                datetime.now().isoformat(),
                preamble_data.created_by
            ))

            conn.commit()
            logger.info(f"Created preamble: {machine_name}")
            return self.get_preamble(preamble_id)
        except Exception as e:
            conn.rollback()
            raise ValueError(f"Failed to create preamble: {str(e)}")
        finally:
            conn.close()

    def get_preamble(self, preamble_id: int) -> Optional[PreambleResponse]:
        """Get a preamble by ID with its active version."""
        conn = self.db.conn
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, machine_name, scope, page_type_code, state_code,
                   project_id, created_via, created_at, created_by
            FROM preambles
            WHERE id = ?
        """, (preamble_id,))

        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        preamble = PreambleResponse(
            id=row[0],
            name=row[1],
            machine_name=row[2],
            scope=row[3],
            page_type_code=row[4],
            state_code=row[5],
            project_id=row[6],
            created_via=row[7],
            created_at=datetime.fromisoformat(row[8]),
            created_by=row[9]
        )

        # Get active version
        cursor.execute("""
            SELECT id, preamble_id, version_number, preamble_text, change_summary,
                   status, created_at, created_by
            FROM preamble_versions
            WHERE preamble_id = ? AND status = 'active'
            ORDER BY version_number DESC
            LIMIT 1
        """, (preamble_id,))

        version_row = cursor.fetchone()
        conn.close()

        if version_row:
            preamble.active_version = PreambleVersionResponse(
                id=version_row[0],
                preamble_id=version_row[1],
                version_number=version_row[2],
                preamble_text=version_row[3],
                change_summary=version_row[4],
                status=version_row[5],
                created_at=datetime.fromisoformat(version_row[6]),
                created_by=version_row[7]
            )

        return preamble

    def list_preambles(
        self,
        scope: Optional[str] = None,
        state_code: Optional[str] = None,
        page_type_code: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> List[PreambleResponse]:
        """List preambles with optional filters."""
        cursor = self.db.conn.cursor()

        query = """
            SELECT id, name, machine_name, scope, page_type_code, state_code,
                   project_id, created_via, created_at, created_by
            FROM preambles
            WHERE 1=1
        """

        params = []

        if scope:
            query += " AND scope = ?"
            params.append(scope)

        if state_code:
            query += " AND state_code = ?"
            params.append(state_code.upper())

        if page_type_code:
            query += " AND page_type_code = ?"
            params.append(page_type_code)

        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)

        query += " ORDER BY scope, state_code, page_type_code, created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [
            self.get_preamble(row[0])
            for row in rows
        ]

    # Preamble Versions
    def create_version(self, version_data: PreambleVersionCreate) -> PreambleVersionResponse:
        """Create a new preamble version (draft by default if not first)."""
        conn = self.db.conn
        cursor = conn.cursor()

        try:
            # Get the next version number
            cursor.execute("""
                SELECT MAX(version_number) FROM preamble_versions
                WHERE preamble_id = ?
            """, (version_data.preamble_id,))

            max_version = cursor.fetchone()[0]
            next_version = (max_version or 0) + 1

            # First version is active, subsequent versions are draft
            status = 'active' if next_version == 1 else 'draft'

            cursor.execute("""
                INSERT INTO preamble_versions (
                    preamble_id, version_number, preamble_text, change_summary,
                    status, created_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                version_data.preamble_id,
                next_version,
                version_data.preamble_text,
                version_data.change_summary,
                status,
                datetime.now().isoformat(),
                version_data.created_by
            ))

            conn.commit()
            version_id = cursor.lastrowid
            logger.info(f"Created version {next_version} for preamble {version_data.preamble_id}")
            return self.get_version(version_id)
        except Exception as e:
            conn.rollback()
            raise ValueError(f"Failed to create version: {str(e)}")
        finally:
            conn.close()

    def get_version(self, version_id: int) -> Optional[PreambleVersionResponse]:
        """Get a preamble version by ID."""
        conn = self.db.conn
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, preamble_id, version_number, preamble_text, change_summary,
                   status, created_at, created_by
            FROM preamble_versions
            WHERE id = ?
        """, (version_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return PreambleVersionResponse(
                id=row[0],
                preamble_id=row[1],
                version_number=row[2],
                preamble_text=row[3],
                change_summary=row[4],
                status=row[5],
                created_at=datetime.fromisoformat(row[6]),
                created_by=row[7]
            )
        return None

    def list_versions(self, preamble_id: int) -> List[PreambleVersionResponse]:
        """List all versions of a preamble."""
        conn = self.db.conn
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, preamble_id, version_number, preamble_text, change_summary,
                   status, created_at, created_by
            FROM preamble_versions
            WHERE preamble_id = ?
            ORDER BY version_number DESC
        """, (preamble_id,))

        rows = cursor.fetchall()
        conn.close()

        return [
            PreambleVersionResponse(
                id=row[0],
                preamble_id=row[1],
                version_number=row[2],
                preamble_text=row[3],
                change_summary=row[4],
                status=row[5],
                created_at=datetime.fromisoformat(row[6]),
                created_by=row[7]
            )
            for row in rows
        ]

    def activate_version(self, version_id: int) -> PreambleVersionResponse:
        """Activate a version (retire current active version)."""
        conn = self.db.conn
        cursor = conn.cursor()

        try:
            # Get the version to activate
            cursor.execute("SELECT preamble_id FROM preamble_versions WHERE id = ?", (version_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Version {version_id} not found")

            preamble_id = row[0]

            # Retire current active version
            cursor.execute("""
                UPDATE preamble_versions
                SET status = 'retired'
                WHERE preamble_id = ? AND status = 'active'
            """, (preamble_id,))

            # Activate new version
            cursor.execute("""
                UPDATE preamble_versions
                SET status = 'active'
                WHERE id = ?
            """, (version_id,))

            conn.commit()

            # Invalidate caches that depend on this version
            self.composition_service.invalidate_caches_for_version(version_id)

            logger.info(f"Activated version {version_id} for preamble {preamble_id}")
            return self.get_version(version_id)
        except Exception as e:
            conn.rollback()
            raise ValueError(f"Failed to activate version: {str(e)}")
        finally:
            conn.close()

    # Test Runs
    def create_test_run(self, test_data: PreambleTestRunCreate) -> PreambleTestRunResponse:
        """Create a new test run record."""
        conn = self.db.conn
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO preamble_test_runs (
                    preamble_version_id, url_id, run_date, score_achieved,
                    violations_found, confidence_score, token_count, cost,
                    duration_seconds, model_used, false_positive, false_negative
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test_data.preamble_version_id,
                test_data.url_id,
                datetime.now().isoformat(),
                test_data.score_achieved,
                test_data.violations_found,
                test_data.confidence_score,
                test_data.token_count,
                test_data.cost,
                test_data.duration_seconds,
                test_data.model_used,
                test_data.false_positive,
                test_data.false_negative
            ))

            conn.commit()
            test_id = cursor.lastrowid

            # Update performance metrics
            self._update_performance_metrics(test_data.preamble_version_id)

            logger.info(f"Created test run {test_id} for version {test_data.preamble_version_id}")
            return self.get_test_run(test_id)
        except Exception as e:
            conn.rollback()
            raise ValueError(f"Failed to create test run: {str(e)}")
        finally:
            conn.close()

    def get_test_run(self, test_id: int) -> Optional[PreambleTestRunResponse]:
        """Get a test run by ID."""
        conn = self.db.conn
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, preamble_version_id, url_id, run_date, score_achieved,
                   violations_found, confidence_score, token_count, cost,
                   duration_seconds, model_used, false_positive, false_negative
            FROM preamble_test_runs
            WHERE id = ?
        """, (test_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return PreambleTestRunResponse(
                id=row[0],
                preamble_version_id=row[1],
                url_id=row[2],
                run_date=datetime.fromisoformat(row[3]),
                score_achieved=row[4],
                violations_found=row[5],
                confidence_score=row[6],
                token_count=row[7],
                cost=row[8],
                duration_seconds=row[9],
                model_used=row[10],
                false_positive=row[11],
                false_negative=row[12]
            )
        return None

    def list_test_runs(
        self,
        preamble_version_id: Optional[int] = None
    ) -> List[PreambleTestRunResponse]:
        """List test runs, optionally filtered by version."""
        conn = self.db.conn
        cursor = conn.cursor()

        if preamble_version_id:
            cursor.execute("""
                SELECT id, preamble_version_id, url_id, run_date, score_achieved,
                       violations_found, confidence_score, token_count, cost,
                       duration_seconds, model_used, false_positive, false_negative
                FROM preamble_test_runs
                WHERE preamble_version_id = ?
                ORDER BY run_date DESC
            """, (preamble_version_id,))
        else:
            cursor.execute("""
                SELECT id, preamble_version_id, url_id, run_date, score_achieved,
                       violations_found, confidence_score, token_count, cost,
                       duration_seconds, model_used, false_positive, false_negative
                FROM preamble_test_runs
                ORDER BY run_date DESC
            """)

        rows = cursor.fetchall()
        conn.close()

        return [
            PreambleTestRunResponse(
                id=row[0],
                preamble_version_id=row[1],
                url_id=row[2],
                run_date=datetime.fromisoformat(row[3]),
                score_achieved=row[4],
                violations_found=row[5],
                confidence_score=row[6],
                token_count=row[7],
                cost=row[8],
                duration_seconds=row[9],
                model_used=row[10],
                false_positive=row[11],
                false_negative=row[12]
            )
            for row in rows
        ]

    def get_version_performance(
        self,
        preamble_version_id: int
    ) -> Optional[PreambleVersionPerformanceResponse]:
        """Get performance metrics for a version."""
        conn = self.db.conn
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, preamble_version_id, test_runs_count, avg_score, score_stddev,
                   avg_confidence, false_positive_rate, false_negative_rate,
                   avg_cost, avg_duration_seconds, last_tested_at
            FROM preamble_version_performance
            WHERE preamble_version_id = ?
        """, (preamble_version_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return PreambleVersionPerformanceResponse(
                id=row[0],
                preamble_version_id=row[1],
                test_runs_count=row[2],
                avg_score=row[3],
                score_stddev=row[4],
                avg_confidence=row[5],
                false_positive_rate=row[6],
                false_negative_rate=row[7],
                avg_cost=row[8],
                avg_duration_seconds=row[9],
                last_tested_at=datetime.fromisoformat(row[10]) if row[10] else None
            )
        return None

    # Helper methods
    def _generate_machine_name(
        self,
        scope: str,
        state_code: Optional[str],
        page_type_code: Optional[str],
        project_id: Optional[int],
        created_via: str
    ) -> str:
        """Generate a machine name for a preamble."""
        parts = []

        if scope == 'universal':
            parts.append('UNIVERSAL')
        elif scope == 'state' and state_code:
            parts.append(state_code.upper())
        elif scope == 'page_type':
            if state_code:
                parts.append(state_code.upper())
            if page_type_code:
                parts.append(page_type_code)
        elif scope == 'project' and project_id:
            parts.append(f'PROJECT_{project_id}')
            if page_type_code:
                parts.append(page_type_code)

        if created_via == 'project_override':
            parts.append('OVERRIDE')
        else:
            parts.append('DEFAULT')

        return '_'.join(parts)

    def _update_performance_metrics(self, preamble_version_id: int):
        """Recalculate and update performance metrics for a version."""
        conn = self.db.conn
        cursor = conn.cursor()

        try:
            # Calculate metrics from test runs
            cursor.execute("""
                SELECT
                    COUNT(*) as run_count,
                    AVG(score_achieved) as avg_score,
                    AVG(confidence_score) as avg_confidence,
                    AVG(CASE WHEN false_positive = 1 THEN 1.0 ELSE 0.0 END) as fp_rate,
                    AVG(CASE WHEN false_negative = 1 THEN 1.0 ELSE 0.0 END) as fn_rate,
                    AVG(cost) as avg_cost,
                    AVG(duration_seconds) as avg_duration,
                    MAX(run_date) as last_test
                FROM preamble_test_runs
                WHERE preamble_version_id = ?
            """, (preamble_version_id,))

            row = cursor.fetchone()

            if row and row[0] > 0:
                # Calculate standard deviation
                cursor.execute("""
                    SELECT AVG((score_achieved - ?) * (score_achieved - ?))
                    FROM preamble_test_runs
                    WHERE preamble_version_id = ? AND score_achieved IS NOT NULL
                """, (row[1], row[1], preamble_version_id))

                variance = cursor.fetchone()[0]
                stddev = (variance ** 0.5) if variance else None

                # Insert or update performance record
                cursor.execute("""
                    INSERT INTO preamble_version_performance (
                        preamble_version_id, test_runs_count, avg_score, score_stddev,
                        avg_confidence, false_positive_rate, false_negative_rate,
                        avg_cost, avg_duration_seconds, last_tested_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(preamble_version_id) DO UPDATE SET
                        test_runs_count = excluded.test_runs_count,
                        avg_score = excluded.avg_score,
                        score_stddev = excluded.score_stddev,
                        avg_confidence = excluded.avg_confidence,
                        false_positive_rate = excluded.false_positive_rate,
                        false_negative_rate = excluded.false_negative_rate,
                        avg_cost = excluded.avg_cost,
                        avg_duration_seconds = excluded.avg_duration_seconds,
                        last_tested_at = excluded.last_tested_at
                """, (
                    preamble_version_id,
                    row[0],  # run_count
                    row[1],  # avg_score
                    stddev,
                    row[2],  # avg_confidence
                    row[3],  # fp_rate
                    row[4],  # fn_rate
                    row[5],  # avg_cost
                    row[6],  # avg_duration
                    row[7]   # last_test
                ))

                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to update performance metrics: {str(e)}")
        finally:
            conn.close()
