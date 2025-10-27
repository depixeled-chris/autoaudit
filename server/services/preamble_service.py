"""Preamble composition and caching service."""

import hashlib
import json
from typing import Optional, Dict, List
from jinja2 import Template
from datetime import datetime
import logging

from core.database import ComplianceDatabase

logger = logging.getLogger(__name__)


class PreambleService:
    """Service for composing and caching preambles."""

    def __init__(self, db: ComplianceDatabase):
        """Initialize service with database."""
        self.db = db

    def compose_preamble(
        self,
        project_id: int,
        page_type_code: str,
        state_code: Optional[str] = None
    ) -> str:
        """
        Compose a preamble for a specific project and page type.

        Hierarchy: Universal → State → Page Type → Project

        Args:
            project_id: Project ID
            page_type_code: Page type code (e.g., 'VDP', 'HOMEPAGE')
            state_code: State code (optional, will get from project if not provided)

        Returns:
            Composed preamble text
        """
        # Get project details if state not provided
        if not state_code:
            project = self.db.get_project(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            state_code = project['state_code']

        # Get active preamble versions for composition
        universal_version = self._get_active_version('universal')
        state_version = self._get_active_version('state', state_code=state_code)
        page_type_version = self._get_active_version('page_type', page_type_code=page_type_code, state_code=state_code)
        project_version = self._get_active_version('project', project_id=project_id, page_type_code=page_type_code)

        # Get default template
        template_data = self._get_default_template()
        if not template_data:
            raise ValueError("No default preamble template found")

        # Generate cache key
        cache_hash = self._generate_cache_hash(
            template_id=template_data['id'],
            universal_version_id=universal_version['id'] if universal_version else None,
            state_version_id=state_version['id'] if state_version else None,
            page_type_version_id=page_type_version['id'] if page_type_version else None,
            project_version_id=project_version['id'] if project_version else None
        )

        # Check cache
        cached = self._get_cached_composition(cache_hash)
        if cached:
            logger.info(f"Cache hit for composition {cache_hash}")
            self._update_cache_hit(cached['id'])
            return cached['composed_text']

        # Compose from template
        logger.info(f"Cache miss - composing new preamble for {page_type_code} in project {project_id}")
        composed_text = self._compose_from_template(
            template_structure=template_data['template_structure'],
            universal_text=universal_version['preamble_text'] if universal_version else '',
            state_text=state_version['preamble_text'] if state_version else '',
            page_type_text=page_type_version['preamble_text'] if page_type_version else '',
            project_text=project_version['preamble_text'] if project_version else '',
            state_code=state_code,
            page_type=page_type_code
        )

        # Cache the result
        self._cache_composition(
            cache_hash=cache_hash,
            template_id=template_data['id'],
            universal_version_id=universal_version['id'] if universal_version else None,
            state_version_id=state_version['id'] if state_version else None,
            page_type_version_id=page_type_version['id'] if page_type_version else None,
            project_version_id=project_version['id'] if project_version else None,
            composed_text=composed_text
        )

        return composed_text

    def invalidate_caches_for_version(self, preamble_version_id: int):
        """
        Invalidate all cached compositions that depend on this version.

        Args:
            preamble_version_id: Version ID that changed
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Find all compositions that depend on this version
        cursor.execute("""
            SELECT DISTINCT composition_id
            FROM preamble_composition_deps
            WHERE depends_on_version_id = ?
        """, (preamble_version_id,))

        composition_ids = [row[0] for row in cursor.fetchall()]

        if composition_ids:
            placeholders = ','.join('?' * len(composition_ids))
            cursor.execute(f"""
                DELETE FROM preamble_compositions
                WHERE id IN ({placeholders})
            """, composition_ids)
            conn.commit()
            logger.info(f"Invalidated {len(composition_ids)} cached compositions")

        conn.close()

    def _get_active_version(
        self,
        scope: str,
        state_code: Optional[str] = None,
        page_type_code: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> Optional[Dict]:
        """Get active preamble version for a given scope."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # First, check for project-level override
        if scope == 'project' and project_id and page_type_code:
            cursor.execute("""
                SELECT pv.id, pv.preamble_id, pv.version_number, pv.preamble_text, pv.status
                FROM project_page_type_preambles pptp
                JOIN preamble_versions pv ON pptp.active_version_id = pv.id
                WHERE pptp.project_id = ? AND pptp.page_type_code = ?
            """, (project_id, page_type_code))
            row = cursor.fetchone()
            if row:
                conn.close()
                return {
                    'id': row[0],
                    'preamble_id': row[1],
                    'version_number': row[2],
                    'preamble_text': row[3],
                    'status': row[4]
                }
            # No project override - return None so we use default
            conn.close()
            return None

        # Build query based on scope
        if scope == 'universal':
            cursor.execute("""
                SELECT pv.id, pv.preamble_id, pv.version_number, pv.preamble_text, pv.status
                FROM preambles p
                JOIN preamble_versions pv ON p.id = pv.preamble_id
                WHERE p.scope = 'universal' AND pv.status = 'active'
                ORDER BY pv.version_number DESC
                LIMIT 1
            """)
        elif scope == 'state' and state_code:
            cursor.execute("""
                SELECT pv.id, pv.preamble_id, pv.version_number, pv.preamble_text, pv.status
                FROM preambles p
                JOIN preamble_versions pv ON p.id = pv.preamble_id
                WHERE p.scope = 'state' AND p.state_code = ? AND pv.status = 'active'
                ORDER BY pv.version_number DESC
                LIMIT 1
            """, (state_code,))
        elif scope == 'page_type' and page_type_code:
            # Check for state-specific page type preamble first
            if state_code:
                cursor.execute("""
                    SELECT pv.id, pv.preamble_id, pv.version_number, pv.preamble_text, pv.status
                    FROM preambles p
                    JOIN preamble_versions pv ON p.id = pv.preamble_id
                    WHERE p.scope = 'page_type'
                      AND p.page_type_code = ?
                      AND p.state_code = ?
                      AND pv.status = 'active'
                    ORDER BY pv.version_number DESC
                    LIMIT 1
                """, (page_type_code, state_code))
                row = cursor.fetchone()
                if row:
                    conn.close()
                    return {
                        'id': row[0],
                        'preamble_id': row[1],
                        'version_number': row[2],
                        'preamble_text': row[3],
                        'status': row[4]
                    }

            # Fall back to default page type preamble
            cursor.execute("""
                SELECT pv.id, pv.preamble_id, pv.version_number, pv.preamble_text, pv.status
                FROM default_page_type_preambles dptp
                JOIN preamble_versions pv ON dptp.active_version_id = pv.id
                WHERE dptp.page_type_code = ?
            """, (page_type_code,))
        else:
            conn.close()
            return None

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row[0],
                'preamble_id': row[1],
                'version_number': row[2],
                'preamble_text': row[3],
                'status': row[4]
            }
        return None

    def _get_default_template(self) -> Optional[Dict]:
        """Get the default preamble template."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, template_structure
            FROM preamble_templates
            WHERE is_default = 1
            LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row[0],
                'name': row[1],
                'template_structure': row[2]
            }
        return None

    def _compose_from_template(
        self,
        template_structure: str,
        universal_text: str,
        state_text: str,
        page_type_text: str,
        project_text: str,
        state_code: str,
        page_type: str
    ) -> str:
        """Compose preamble using Jinja2 template."""
        template = Template(template_structure)

        return template.render(
            universal_preamble=universal_text,
            state_preamble=state_text,
            page_type_preamble=page_type_text,
            project_preamble=project_text,
            state_code=state_code,
            page_type=page_type
        )

    def _generate_cache_hash(
        self,
        template_id: int,
        universal_version_id: Optional[int],
        state_version_id: Optional[int],
        page_type_version_id: Optional[int],
        project_version_id: Optional[int]
    ) -> str:
        """Generate a hash for cache lookup."""
        cache_key = {
            'template_id': template_id,
            'universal_version_id': universal_version_id,
            'state_version_id': state_version_id,
            'page_type_version_id': page_type_version_id,
            'project_version_id': project_version_id
        }

        # Create deterministic hash
        key_string = json.dumps(cache_key, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def _get_cached_composition(self, cache_hash: str) -> Optional[Dict]:
        """Retrieve cached composition by hash."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, composed_text, hit_count
            FROM preamble_compositions
            WHERE composition_hash = ?
        """, (cache_hash,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row[0],
                'composed_text': row[1],
                'hit_count': row[2]
            }
        return None

    def _cache_composition(
        self,
        cache_hash: str,
        template_id: int,
        universal_version_id: Optional[int],
        state_version_id: Optional[int],
        page_type_version_id: Optional[int],
        project_version_id: Optional[int],
        composed_text: str
    ):
        """Cache a composed preamble."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Insert composition
        cursor.execute("""
            INSERT INTO preamble_compositions (
                composition_hash,
                template_id,
                universal_version_id,
                state_version_id,
                page_type_version_id,
                project_version_id,
                composed_text,
                created_at,
                last_used_at,
                hit_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            cache_hash,
            template_id,
            universal_version_id,
            state_version_id,
            page_type_version_id,
            project_version_id,
            composed_text,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

        composition_id = cursor.lastrowid

        # Insert dependency records for cache invalidation
        for version_id in [universal_version_id, state_version_id, page_type_version_id, project_version_id]:
            if version_id:
                cursor.execute("""
                    INSERT INTO preamble_composition_deps (composition_id, depends_on_version_id)
                    VALUES (?, ?)
                """, (composition_id, version_id))

        conn.commit()
        conn.close()

        logger.info(f"Cached composition {cache_hash} with {composition_id}")

    def _update_cache_hit(self, composition_id: int):
        """Update cache hit count and last_used_at."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE preamble_compositions
            SET hit_count = hit_count + 1,
                last_used_at = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), composition_id))

        conn.commit()
        conn.close()
