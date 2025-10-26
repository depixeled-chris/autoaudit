"""Service for managing compliance scans with batch and immediate processing."""

import sys
from pathlib import Path
from typing import Dict, Optional, List
import logging
from datetime import datetime
import asyncio

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import ComplianceDatabase
from core.main_hybrid import HybridComplianceChecker
from services.base_service import BaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScanService(BaseService):
    """Service for compliance scanning with batch and immediate modes."""

    def __init__(self, db: ComplianceDatabase):
        """Initialize scan service."""
        super().__init__(db)

    async def force_rescan_immediate(
        self,
        url_id: int,
        skip_visual: bool = False
    ) -> Dict:
        """
        Force an immediate scan for non-inventory URLs.

        This bypasses batch processing and runs the scan synchronously.
        Should only be used for:
        - VDP (vehicle detail pages)
        - Homepage scans
        - Manual forced scans on non-inventory pages

        Args:
            url_id: ID of the URL to scan
            skip_visual: Whether to skip visual verification

        Returns:
            Dictionary with check results

        Raises:
            ValueError: If URL is inventory type or not found
        """
        logger.info(f"Starting immediate rescan for URL ID: {url_id}")

        # Get URL details
        url_data = self.db.get_url(url_id=url_id)
        if not url_data:
            raise ValueError(f"URL not found: {url_id}")

        # Force rescan works regardless of active status
        # Active status only controls automatic scheduled scans

        # Check if URL type allows immediate scan
        url_type = url_data.get('url_type', '').lower()
        if url_type == 'inventory':
            raise ValueError(
                "Inventory URLs must use batch processing. "
                "Use schedule_batch_scan() instead."
            )

        # Get project to determine state code
        project_id = url_data['project_id']
        if not project_id:
            raise ValueError("URL must be associated with a project")

        project = self.db.get_project(project_id=project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        state_code = project['state_code']
        url = url_data['url']
        url_type = url_data.get('url_type', 'VDP')  # Default to VDP if not specified

        try:
            # Initialize checker
            checker = HybridComplianceChecker(
                state_code=state_code,
                output_dir="reports"
            )

            # Run immediate check
            logger.info(f"Running immediate check for {url} (Type: {url_type})")
            result = await checker.check_url(
                url=url,
                save_formats=['json', 'markdown'],
                skip_visual=skip_visual,
                url_type=url_type
            )

            # Save to database
            check_id = self.db.save_compliance_check(
                url=url,
                url_id=url_id,
                state_code=state_code,
                template_id=result.get('template_id'),
                overall_score=result.get('overall_compliance_score', 0),
                compliance_status=result.get('compliance_status', 'UNKNOWN'),
                summary=result.get('summary', ''),
                llm_input_path=result.get('report_paths', {}).get('llm_input'),
                report_path=result.get('report_paths', {}).get('markdown'),
                text_analysis_tokens=result.get('text_analysis_tokens', 0),
                visual_tokens=result.get('visual_tokens', 0),
                total_tokens=result.get('total_tokens', 0)
            )

            # Save violations
            for violation in result.get('violations', []):
                self.db.save_violation(
                    check_id=check_id,
                    category=violation.get('category', 'unknown'),
                    severity=violation.get('severity', 'unknown'),
                    rule_violated=violation.get('rule_violated', ''),
                    rule_key=violation.get('rule_key'),
                    confidence=violation.get('confidence'),
                    needs_visual_verification=violation.get('needs_visual_verification', False),
                    explanation=violation.get('explanation'),
                    evidence=violation.get('evidence')
                )

            # Save visual verifications
            for visual in result.get('visual_verifications', []):
                self.db.save_visual_verification(
                    check_id=check_id,
                    rule_key=visual.get('rule_key', ''),
                    rule_text=visual.get('rule', ''),
                    is_compliant=visual.get('is_compliant', False),
                    confidence=visual.get('confidence', 0.0),
                    verification_method=visual.get('verification_method', 'visual'),
                    visual_evidence=visual.get('visual_evidence'),
                    proximity_description=visual.get('proximity_description'),
                    screenshot_path=visual.get('screenshot_path'),
                    cached=visual.get('cached', False),
                    tokens_used=visual.get('tokens_used', 0)
                )

            # Update URL last_checked timestamp
            cursor = self.db.conn.cursor()
            cursor.execute(
                "UPDATE urls SET last_checked = CURRENT_TIMESTAMP WHERE id = ?",
                (url_id,)
            )
            self.db.conn.commit()

            logger.info(f"Immediate scan completed successfully: check_id={check_id}")

            return {
                "check_id": check_id,
                "url_id": url_id,
                "url": url,
                "scan_type": "immediate",
                "compliance_status": result.get('compliance_status', 'UNKNOWN'),
                "overall_score": result.get('overall_compliance_score', 0),
                "violations_count": len(result.get('violations', [])),
                "completed_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Immediate scan failed for URL {url_id}: {str(e)}")
            raise ValueError(f"Scan failed: {str(e)}")

    async def schedule_batch_scan(
        self,
        url_ids: List[int],
        batch_name: Optional[str] = None
    ) -> Dict:
        """
        Schedule a batch scan for inventory or scheduled scans.

        Uses OpenAI's Batch API for cost-effective processing of multiple URLs.
        Should be used for:
        - Inventory page scans
        - Scheduled periodic scans
        - Bulk scanning operations

        Args:
            url_ids: List of URL IDs to scan
            batch_name: Optional name for the batch

        Returns:
            Dictionary with batch details

        Raises:
            ValueError: If no valid URLs found
        """
        logger.info(f"Scheduling batch scan for {len(url_ids)} URLs")

        # Validate all URLs
        valid_urls = []
        for url_id in url_ids:
            url_data = self.db.get_url(url_id=url_id)
            if url_data and url_data['active']:
                valid_urls.append(url_data)
            else:
                logger.warning(f"Skipping invalid or inactive URL: {url_id}")

        if not valid_urls:
            raise ValueError("No valid active URLs found for batch scan")

        # TODO: Implement OpenAI Batch API integration
        # For now, just mark URLs as pending batch scan
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        for url_data in valid_urls:
            cursor = self.db.conn.cursor()
            cursor.execute(
                """
                UPDATE urls
                SET last_checked = NULL
                WHERE id = ?
                """,
                (url_data['id'],)
            )
        self.db.conn.commit()

        logger.info(f"Batch scan scheduled: {batch_id} ({len(valid_urls)} URLs)")

        return {
            "batch_id": batch_id,
            "batch_name": batch_name or batch_id,
            "scan_type": "batch",
            "url_count": len(valid_urls),
            "scheduled_at": datetime.now().isoformat(),
            "status": "scheduled",
            "message": "Batch scan scheduled. OpenAI Batch API integration pending."
        }

    def get_urls_needing_scan(
        self,
        project_id: Optional[int] = None,
        url_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Get URLs that need scanning based on their check frequency.

        Args:
            project_id: Optional project filter
            url_type: Optional URL type filter

        Returns:
            List of URL records needing scans
        """
        cursor = self.db.conn.cursor()

        # Build query to find URLs that:
        # 1. Are active
        # 2. Have never been checked OR
        # 3. Last check was more than check_frequency_hours ago
        query = """
            SELECT * FROM urls
            WHERE active = 1
            AND (
                last_checked IS NULL
                OR datetime(last_checked, '+' || check_frequency_hours || ' hours') < datetime('now')
            )
        """
        params = []

        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)

        if url_type:
            query += " AND url_type = ?"
            params.append(url_type)

        query += " ORDER BY last_checked ASC NULLS FIRST"

        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        urls = [dict(zip(columns, row)) for row in cursor.fetchall()]

        logger.info(f"Found {len(urls)} URLs needing scan")
        return urls
