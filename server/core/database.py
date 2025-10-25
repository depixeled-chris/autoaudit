"""SQLite database management for compliance checking."""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComplianceDatabase:
    """Manages SQLite database for compliance checking system."""

    def __init__(self, db_path: str = "compliance.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        # check_same_thread=False allows connection to be used across threads
        # This is safe with FastAPI's dependency injection since each request gets its own instance
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self._create_tables()
        logger.info(f"Database initialized: {db_path}")

    def _create_tables(self):
        """Create database schema if it doesn't exist."""
        cursor = self.conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                state_code TEXT NOT NULL,
                base_url TEXT,
                screenshot_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migration: Add screenshot_path if it doesn't exist
        cursor.execute("PRAGMA table_info(projects)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'screenshot_path' not in columns:
            cursor.execute("ALTER TABLE projects ADD COLUMN screenshot_path TEXT")
            logger.info("Added screenshot_path column to projects table")

        # Templates table (for compliance caching)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id TEXT NOT NULL UNIQUE,
                platform TEXT NOT NULL,
                template_type TEXT DEFAULT 'compliance',
                config JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Template rules (cached compliance decisions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS template_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id TEXT NOT NULL,
                rule_key TEXT NOT NULL,
                status TEXT NOT NULL,
                confidence REAL NOT NULL,
                verification_method TEXT,
                notes TEXT,
                verified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (template_id) REFERENCES templates(template_id),
                UNIQUE(template_id, rule_key)
            )
        """)

        # URLs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                url TEXT NOT NULL UNIQUE,
                url_type TEXT DEFAULT 'vdp',
                template_id TEXT,
                platform TEXT,
                active BOOLEAN DEFAULT 1,
                check_frequency_hours INTEGER DEFAULT 24,
                last_checked TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (template_id) REFERENCES templates(template_id)
            )
        """)

        # Compliance checks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compliance_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                state_code TEXT NOT NULL,
                template_id TEXT,
                overall_score INTEGER,
                compliance_status TEXT,
                summary TEXT,
                llm_input_path TEXT,
                report_path TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (url_id) REFERENCES urls(id),
                FOREIGN KEY (template_id) REFERENCES templates(template_id)
            )
        """)

        # Violations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                rule_violated TEXT NOT NULL,
                rule_key TEXT,
                confidence REAL,
                needs_visual_verification BOOLEAN DEFAULT 0,
                explanation TEXT,
                evidence TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (check_id) REFERENCES compliance_checks(id)
            )
        """)

        # Visual verifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS visual_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_id INTEGER NOT NULL,
                violation_id INTEGER,
                rule_key TEXT NOT NULL,
                rule_text TEXT,
                is_compliant BOOLEAN NOT NULL,
                confidence REAL NOT NULL,
                verification_method TEXT DEFAULT 'visual',
                visual_evidence TEXT,
                proximity_description TEXT,
                screenshot_path TEXT,
                cached BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (check_id) REFERENCES compliance_checks(id),
                FOREIGN KEY (violation_id) REFERENCES violations(id)
            )
        """)

        # Extraction templates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extraction_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id TEXT NOT NULL UNIQUE,
                platform TEXT NOT NULL,
                selectors JSON NOT NULL,
                cleanup_rules JSON,
                extraction_order JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migrations - add columns if they don't exist
        try:
            cursor.execute("ALTER TABLE projects ADD COLUMN base_url TEXT")
            self.conn.commit()
            logger.info("Added base_url column to projects table")
        except sqlite3.OperationalError:
            # Column already exists
            pass

        self.conn.commit()
        logger.info("Database schema created/verified")

    # ==================== User Management ====================

    def create_user(self, email: str, password_hash: str, full_name: str = None) -> int:
        """Create a new user."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO users (email, password_hash, full_name)
            VALUES (?, ?, ?)
        """, (email, password_hash, full_name))
        self.conn.commit()
        logger.info(f"Created user: {email}")
        return cursor.lastrowid

    def get_user(self, user_id: int = None, email: str = None) -> Optional[Dict]:
        """Get user by ID or email."""
        cursor = self.conn.cursor()
        if user_id:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        elif email:
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        else:
            return None

        row = cursor.fetchone()
        return dict(row) if row else None

    def update_user(self, user_id: int, full_name: str = None, password_hash: str = None):
        """Update user information."""
        cursor = self.conn.cursor()
        if full_name and password_hash:
            cursor.execute("""
                UPDATE users SET full_name = ?, password_hash = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (full_name, password_hash, user_id))
        elif full_name:
            cursor.execute("""
                UPDATE users SET full_name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
            """, (full_name, user_id))
        elif password_hash:
            cursor.execute("""
                UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
            """, (password_hash, user_id))
        self.conn.commit()

    # ==================== Project Management ====================

    def create_project(self, name: str, state_code: str, description: str = None, base_url: str = None) -> int:
        """Create a new project."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO projects (name, state_code, description, base_url)
            VALUES (?, ?, ?, ?)
        """, (name, state_code, description, base_url))
        self.conn.commit()
        logger.info(f"Created project: {name}")
        return cursor.lastrowid

    def get_project(self, project_id: int = None, name: str = None) -> Optional[Dict]:
        """Get project by ID or name."""
        cursor = self.conn.cursor()
        if project_id:
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        elif name:
            cursor.execute("SELECT * FROM projects WHERE name = ?", (name,))
        else:
            return None

        row = cursor.fetchone()
        return dict(row) if row else None

    def list_projects(self) -> List[Dict]:
        """List all projects."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    def update_project_screenshot(self, project_id: int, screenshot_path: str) -> bool:
        """Update project screenshot path."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE projects
            SET screenshot_path = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (screenshot_path, project_id))
        self.conn.commit()
        logger.info(f"Updated screenshot for project {project_id}: {screenshot_path}")
        return cursor.rowcount > 0

    # ==================== Template Management ====================

    def save_template(self, template_id: str, platform: str, config: Dict = None) -> int:
        """Save or update a template."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO templates (template_id, platform, config)
            VALUES (?, ?, ?)
            ON CONFLICT(template_id) DO UPDATE SET
                platform = excluded.platform,
                config = excluded.config,
                updated_at = CURRENT_TIMESTAMP
        """, (template_id, platform, json.dumps(config) if config else None))
        self.conn.commit()
        return cursor.lastrowid

    def get_template(self, template_id: str) -> Optional[Dict]:
        """Get template by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM templates WHERE template_id = ?", (template_id,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            if result['config']:
                result['config'] = json.loads(result['config'])
            return result
        return None

    def save_template_rule(
        self,
        template_id: str,
        rule_key: str,
        status: str,
        confidence: float,
        verification_method: str = None,
        notes: str = None
    ):
        """Save or update a cached rule decision for a template."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO template_rules
            (template_id, rule_key, status, confidence, verification_method, notes, verified_date)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(template_id, rule_key) DO UPDATE SET
                status = excluded.status,
                confidence = excluded.confidence,
                verification_method = excluded.verification_method,
                notes = excluded.notes,
                verified_date = CURRENT_TIMESTAMP
        """, (template_id, rule_key, status, confidence, verification_method, notes))
        self.conn.commit()
        logger.info(f"Saved rule {rule_key} for template {template_id}: {status}")

    def get_template_rule(self, template_id: str, rule_key: str) -> Optional[Dict]:
        """Get cached rule decision for a template."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM template_rules
            WHERE template_id = ? AND rule_key = ?
        """, (template_id, rule_key))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_template_rules(self, template_id: str) -> List[Dict]:
        """Get all cached rules for a template."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM template_rules
            WHERE template_id = ?
            ORDER BY verified_date DESC
        """, (template_id,))
        return [dict(row) for row in cursor.fetchall()]

    # ==================== URL Management ====================

    def add_url(
        self,
        url: str,
        project_id: int = None,
        url_type: str = "vdp",
        template_id: str = None,
        platform: str = None,
        check_frequency_hours: int = 24
    ) -> int:
        """Add a URL to monitor."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO urls (project_id, url, url_type, template_id, platform, check_frequency_hours)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                project_id = excluded.project_id,
                template_id = excluded.template_id,
                platform = excluded.platform,
                check_frequency_hours = excluded.check_frequency_hours
        """, (project_id, url, url_type, template_id, platform, check_frequency_hours))
        self.conn.commit()
        return cursor.lastrowid

    def get_url(self, url_id: int = None, url: str = None) -> Optional[Dict]:
        """Get URL by ID or URL string."""
        cursor = self.conn.cursor()
        if url_id:
            cursor.execute("SELECT * FROM urls WHERE id = ?", (url_id,))
        elif url:
            cursor.execute("SELECT * FROM urls WHERE url = ?", (url,))
        else:
            return None

        row = cursor.fetchone()
        return dict(row) if row else None

    def list_urls(self, project_id: int = None, active_only: bool = True) -> List[Dict]:
        """List URLs, optionally filtered by project."""
        cursor = self.conn.cursor()
        if project_id:
            if active_only:
                cursor.execute("SELECT * FROM urls WHERE project_id = ? AND active = 1", (project_id,))
            else:
                cursor.execute("SELECT * FROM urls WHERE project_id = ?", (project_id,))
        else:
            if active_only:
                cursor.execute("SELECT * FROM urls WHERE active = 1")
            else:
                cursor.execute("SELECT * FROM urls")
        return [dict(row) for row in cursor.fetchall()]

    def update_url_last_checked(self, url_id: int):
        """Update last_checked timestamp for a URL."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE urls SET last_checked = CURRENT_TIMESTAMP WHERE id = ?
        """, (url_id,))
        self.conn.commit()

    # ==================== Compliance Check Management ====================

    def save_compliance_check(
        self,
        url: str,
        state_code: str,
        template_id: str,
        overall_score: int,
        compliance_status: str,
        summary: str,
        llm_input_path: str = None,
        report_path: str = None
    ) -> int:
        """Save a compliance check result."""
        # Get or create URL
        url_data = self.get_url(url=url)
        if url_data:
            url_id = url_data['id']
            self.update_url_last_checked(url_id)
        else:
            url_id = self.add_url(url, template_id=template_id)

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO compliance_checks
            (url_id, url, state_code, template_id, overall_score, compliance_status,
             summary, llm_input_path, report_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (url_id, url, state_code, template_id, overall_score, compliance_status,
              summary, llm_input_path, report_path))
        self.conn.commit()
        logger.info(f"Saved compliance check for {url}: {overall_score}/100")
        return cursor.lastrowid

    def get_compliance_check(self, check_id: int) -> Optional[Dict]:
        """Get compliance check by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM compliance_checks WHERE id = ?", (check_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_latest_check(self, url: str) -> Optional[Dict]:
        """Get most recent compliance check for a URL."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM compliance_checks
            WHERE url = ?
            ORDER BY checked_at DESC
            LIMIT 1
        """, (url,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_checks(
        self,
        url_id: int = None,
        state_code: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """List compliance checks with optional filters."""
        cursor = self.conn.cursor()
        query = "SELECT * FROM compliance_checks WHERE 1=1"
        params = []

        if url_id:
            query += " AND url_id = ?"
            params.append(url_id)
        if state_code:
            query += " AND state_code = ?"
            params.append(state_code)

        query += " ORDER BY checked_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    # ==================== Violation Management ====================

    def save_violation(
        self,
        check_id: int,
        category: str,
        severity: str,
        rule_violated: str,
        rule_key: str = None,
        confidence: float = None,
        needs_visual_verification: bool = False,
        explanation: str = None,
        evidence: str = None
    ) -> int:
        """Save a violation."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO violations
            (check_id, category, severity, rule_violated, rule_key, confidence,
             needs_visual_verification, explanation, evidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (check_id, category, severity, rule_violated, rule_key, confidence,
              needs_visual_verification, explanation, evidence))
        self.conn.commit()
        return cursor.lastrowid

    def get_violations(self, check_id: int) -> List[Dict]:
        """Get all violations for a compliance check."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM violations WHERE check_id = ? ORDER BY severity, id
        """, (check_id,))
        return [dict(row) for row in cursor.fetchall()]

    # ==================== Visual Verification Management ====================

    def save_visual_verification(
        self,
        check_id: int,
        rule_key: str,
        rule_text: str,
        is_compliant: bool,
        confidence: float,
        verification_method: str = "visual",
        visual_evidence: str = None,
        proximity_description: str = None,
        screenshot_path: str = None,
        cached: bool = False,
        violation_id: int = None
    ) -> int:
        """Save a visual verification result."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO visual_verifications
            (check_id, violation_id, rule_key, rule_text, is_compliant, confidence,
             verification_method, visual_evidence, proximity_description,
             screenshot_path, cached)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (check_id, violation_id, rule_key, rule_text, is_compliant, confidence,
              verification_method, visual_evidence, proximity_description,
              screenshot_path, cached))
        self.conn.commit()
        return cursor.lastrowid

    def get_visual_verifications(self, check_id: int) -> List[Dict]:
        """Get all visual verifications for a compliance check."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM visual_verifications WHERE check_id = ? ORDER BY id
        """, (check_id,))
        return [dict(row) for row in cursor.fetchall()]

    # ==================== Extraction Template Management ====================

    def save_extraction_template(
        self,
        template_id: str,
        platform: str,
        selectors: Dict,
        cleanup_rules: Dict = None,
        extraction_order: List[str] = None
    ):
        """Save or update an extraction template."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO extraction_templates
            (template_id, platform, selectors, cleanup_rules, extraction_order)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(template_id) DO UPDATE SET
                platform = excluded.platform,
                selectors = excluded.selectors,
                cleanup_rules = excluded.cleanup_rules,
                extraction_order = excluded.extraction_order,
                updated_at = CURRENT_TIMESTAMP
        """, (template_id, platform, json.dumps(selectors),
              json.dumps(cleanup_rules) if cleanup_rules else None,
              json.dumps(extraction_order) if extraction_order else None))
        self.conn.commit()
        logger.info(f"Saved extraction template: {template_id}")

    def get_extraction_template(self, template_id: str) -> Optional[Dict]:
        """Get extraction template by ID."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM extraction_templates WHERE template_id = ?
        """, (template_id,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            result['selectors'] = json.loads(result['selectors'])
            if result['cleanup_rules']:
                result['cleanup_rules'] = json.loads(result['cleanup_rules'])
            if result['extraction_order']:
                result['extraction_order'] = json.loads(result['extraction_order'])
            return result
        return None

    # ==================== Reporting ====================

    def get_project_summary(self, project_id: int) -> Dict:
        """Get summary statistics for a project."""
        cursor = self.conn.cursor()

        # Total URLs
        cursor.execute("""
            SELECT COUNT(*) as total FROM urls WHERE project_id = ? AND active = 1
        """, (project_id,))
        total_urls = cursor.fetchone()[0]

        # Recent checks
        cursor.execute("""
            SELECT
                COUNT(*) as total_checks,
                AVG(overall_score) as avg_score,
                SUM(CASE WHEN compliance_status = 'COMPLIANT' THEN 1 ELSE 0 END) as compliant_count
            FROM compliance_checks c
            JOIN urls u ON c.url_id = u.id
            WHERE u.project_id = ?
        """, (project_id,))
        check_stats = dict(cursor.fetchone())

        # Recent violations
        cursor.execute("""
            SELECT COUNT(*) as total_violations
            FROM violations v
            JOIN compliance_checks c ON v.check_id = c.id
            JOIN urls u ON c.url_id = u.id
            WHERE u.project_id = ?
        """, (project_id,))
        violation_count = cursor.fetchone()[0]

        return {
            "total_urls": total_urls,
            "total_checks": check_stats['total_checks'] or 0,
            "avg_score": round(check_stats['avg_score'], 1) if check_stats['avg_score'] else 0,
            "compliant_count": check_stats['compliant_count'] or 0,
            "total_violations": violation_count or 0
        }

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


def main():
    """Example usage and testing."""
    db = ComplianceDatabase("test_compliance.db")

    # Create a project
    project_id = db.create_project(
        name="AllStar CDJR Muskogee",
        state_code="OK",
        description="Oklahoma dealership compliance monitoring"
    )
    print(f"Created project: {project_id}")

    # Add a URL
    url_id = db.add_url(
        url="https://www.allstarcdjrmuskogee.com/used/Chevrolet/2022-Chevrolet-Silverado-1500-f793dc61ac184236e10863afe4bf9621.htm",
        project_id=project_id,
        template_id="dealer.com_vdp",
        platform="dealer.com"
    )
    print(f"Added URL: {url_id}")

    # Save a template rule
    db.save_template_rule(
        template_id="dealer.com_vdp",
        rule_key="vehicle_id_adjacent",
        status="compliant",
        confidence=0.95,
        verification_method="visual",
        notes="Vehicle ID prominently displayed above price"
    )

    # Save a compliance check
    check_id = db.save_compliance_check(
        url="https://www.allstarcdjrmuskogee.com/used/Chevrolet/2022-Chevrolet-Silverado-1500-f793dc61ac184236e10863afe4bf9621.htm",
        state_code="OK",
        template_id="dealer.com_vdp",
        overall_score=70,
        compliance_status="NEEDS_REVIEW",
        summary="Found 4 violations, 1 visually verified as compliant"
    )
    print(f"Saved check: {check_id}")

    # Get project summary
    summary = db.get_project_summary(project_id)
    print("\nProject Summary:")
    print(json.dumps(summary, indent=2))

    db.close()


if __name__ == "__main__":
    main()
