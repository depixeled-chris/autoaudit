"""Template detection and configuration management."""

import json
from pathlib import Path
from typing import Dict, Optional
import logging
from datetime import datetime
from .database import ComplianceDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TemplateManager:
    """Manages template detection and compliance configuration."""

    def __init__(self, db_path: str = "compliance.db"):
        """
        Initialize template manager with database.

        Args:
            db_path: Path to SQLite database
        """
        self.db = ComplianceDatabase(db_path)
        logger.info(f"TemplateManager initialized with database: {db_path}")

    def detect_template(self, url: str, platform: str, html: str) -> Optional[str]:
        """
        Detect which template a webpage uses.

        Args:
            url: Page URL
            platform: Detected platform (dealer.com, DealerOn, etc.)
            html: Page HTML

        Returns:
            Template ID or None
        """
        # Simple detection based on platform
        if platform == "dealer.com" or "dealer.com" in html:
            return "dealer.com_vdp"
        elif "dealeron" in platform.lower() or "dealeron" in html.lower():
            return "dealeron_vdp"
        elif "cdk" in platform.lower():
            return "cdk_vdp"
        elif "autotrader" in platform.lower():
            return "autotrader_vdp"

        # Fall back to domain-based
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.replace('www.', '')
        return f"custom_{domain}"

    def get_template_config(self, template_id: str) -> Optional[Dict]:
        """
        Get configuration for a template.

        Args:
            template_id: Template identifier

        Returns:
            Template configuration or None
        """
        template = self.db.get_template(template_id)
        if not template:
            return None

        # Load associated rules
        rules = self.db.get_template_rules(template_id)
        known_compliance = {}
        for rule in rules:
            known_compliance[rule['rule_key']] = {
                "status": rule['status'],
                "confidence": rule['confidence'],
                "verified_date": rule['verified_date'],
                "verification_method": rule['verification_method'],
                "notes": rule['notes']
            }

        return {
            "template_id": template['template_id'],
            "platform": template['platform'],
            "known_compliance": known_compliance
        }

    def get_rule_status(self, template_id: str, rule: str) -> Optional[Dict]:
        """
        Get known compliance status for a rule in a template.

        Args:
            template_id: Template identifier
            rule: Rule to check

        Returns:
            Rule status dictionary or None
        """
        rule_data = self.db.get_template_rule(template_id, rule)
        if not rule_data:
            return None

        return {
            "status": rule_data['status'],
            "confidence": rule_data['confidence'],
            "verified_date": rule_data['verified_date'],
            "verification_method": rule_data['verification_method'],
            "notes": rule_data['notes']
        }

    def update_rule_status(
        self,
        template_id: str,
        rule: str,
        status: str,
        confidence: float,
        verification_method: str,
        notes: str = ""
    ):
        """
        Update the compliance status for a rule in a template.

        Args:
            template_id: Template identifier
            rule: Rule key
            status: "compliant", "non_compliant", or "uncertain"
            confidence: Confidence score (0.0-1.0)
            verification_method: "text", "visual", or "human"
            notes: Additional notes
        """
        # Ensure template exists
        template = self.db.get_template(template_id)
        if not template:
            # Create template if it doesn't exist
            from urllib.parse import urlparse
            platform = "unknown"
            self.db.save_template(template_id, platform)
            logger.info(f"Created new template: {template_id}")

        # Save rule to database
        self.db.save_template_rule(
            template_id=template_id,
            rule_key=rule,
            status=status,
            confidence=confidence,
            verification_method=verification_method,
            notes=notes
        )

        logger.info(f"Updated template {template_id}, rule {rule}: {status} ({confidence})")

    def should_skip_visual_verification(
        self,
        template_id: str,
        rule: str,
        confidence_threshold: float = 0.85
    ) -> bool:
        """
        Determine if visual verification can be skipped.

        Args:
            template_id: Template identifier
            rule: Rule to check
            confidence_threshold: Minimum confidence to skip

        Returns:
            True if we can skip visual verification
        """
        rule_status = self.get_rule_status(template_id, rule)
        if not rule_status:
            return False

        # Skip if we have high confidence from previous verification
        if rule_status.get("confidence", 0) >= confidence_threshold:
            logger.info(f"Skipping visual verification for {rule} (cached: {rule_status['status']})")
            return True

        return False

    def create_default_template(self, template_id: str, platform: str):
        """
        Create a default template configuration.

        Args:
            template_id: Template identifier
            platform: Platform name
        """
        self.db.save_template(template_id, platform)
        logger.info(f"Created default template: {template_id}")


def main():
    """Example usage."""
    manager = TemplateManager()

    # Create a sample template
    manager.create_default_template("dealer.com_vdp", "dealer.com")

    # Update a rule status
    manager.update_rule_status(
        template_id="dealer.com_vdp",
        rule="vehicle_id_adjacent_to_price",
        status="compliant",
        confidence=0.95,
        verification_method="visual",
        notes="Vehicle heading always appears directly above price module in dealer.com VDP template"
    )

    # Check if we should skip visual verification
    should_skip = manager.should_skip_visual_verification(
        template_id="dealer.com_vdp",
        rule="vehicle_id_adjacent_to_price"
    )
    print(f"Should skip visual verification: {should_skip}")

    # Get rule status
    status = manager.get_rule_status("dealer.com_vdp", "vehicle_id_adjacent_to_price")
    print(f"Rule status: {status}")


if __name__ == "__main__":
    main()
