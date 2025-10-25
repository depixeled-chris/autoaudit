"""Template-based content extraction for clean, focused analysis."""

import json
from pathlib import Path
from typing import Dict, List, Optional
import logging
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExtractionTemplate:
    """Represents a content extraction template."""

    def __init__(self, config: Dict):
        """
        Initialize extraction template.

        Args:
            config: Template configuration dictionary
        """
        self.template_id = config.get('template_id', 'unknown')
        self.platform = config.get('platform', 'unknown')
        self.selectors = config.get('selectors', {})
        self.cleanup_rules = config.get('cleanup_rules', {})
        self.extraction_order = config.get('extraction_order', [])

    async def extract(self, page) -> Dict[str, str]:
        """
        Extract content from page using template selectors.

        Args:
            page: Playwright page object

        Returns:
            Dictionary of extracted content sections
        """
        extracted = {}

        # Extract each section in order
        for section_name in self.extraction_order:
            selector = self.selectors.get(section_name)
            if selector:
                try:
                    # Try multiple selectors (comma-separated)
                    selectors = [s.strip() for s in selector.split(',')]
                    content = None

                    for sel in selectors:
                        element = await page.query_selector(sel)
                        if element:
                            content = await element.inner_text()
                            break

                    if content:
                        extracted[section_name] = content.strip()
                        logger.debug(f"Extracted {section_name}: {len(content)} chars")
                    else:
                        logger.debug(f"No content found for {section_name}")

                except Exception as e:
                    logger.warning(f"Error extracting {section_name}: {str(e)}")

        return extracted

    async def get_clean_html(self, page) -> str:
        """
        Get cleaned HTML with navigation and noise removed.

        Args:
            page: Playwright page object

        Returns:
            Cleaned HTML string
        """
        # Remove unwanted elements
        remove_selectors = self.cleanup_rules.get('remove_selectors', [])
        for selector in remove_selectors:
            try:
                await page.evaluate(f"""
                    document.querySelectorAll('{selector}').forEach(el => el.remove());
                """)
            except Exception as e:
                logger.debug(f"Could not remove {selector}: {str(e)}")

        # Get remaining HTML
        if self.cleanup_rules.get('keep_only_main_content'):
            # Try to find main content container
            main_selectors = ['main', '.main-content', '#main', '.vehicle-details', '.vdp-container']
            for selector in main_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        return await element.inner_html()
                except:
                    continue

        # Fallback to body
        return await page.content()


class ExtractionTemplateManager:
    """Manages extraction templates with override hierarchy."""

    def __init__(self, db_path: str = "compliance.db"):
        """
        Initialize template manager with database.

        Args:
            db_path: Path to SQLite database
        """
        from database import ComplianceDatabase
        self.db = ComplianceDatabase(db_path)
        self._load_default_templates()
        logger.info(f"ExtractionTemplateManager initialized with database: {db_path}")

    def _load_default_templates(self):
        """Load default templates for common platforms."""
        # Dealer.com template
        dealer_com = {
            "template_id": "dealer.com_vdp",
            "platform": "dealer.com",
            "selectors": {
                "vehicle_heading": ".vehicle-title h1, .vdp-title h1, h1.vehicle-name",
                "price_primary": ".pricing-module .price, .internet-price, .final-price",
                "price_section": ".pricing-module, .price-section, .vehicle-pricing",
                "dealer_name": ".dealer-info .name, .dealership-name",
                "stock_number": ".stock-number, .vin-stock .stock",
                "vin": ".vin-number, .vehicle-vin",
                "disclaimers": ".legal-disclaimers, .pricing-disclaimers, .disclaimer-text",
                "description": ".vehicle-description, .vehicle-overview",
                "features": ".vehicle-features, .equipment-list, .features-list"
            },
            "cleanup_rules": {
                "remove_selectors": [
                    "nav", "header.site-header", "footer.site-footer",
                    ".navigation", ".main-menu", ".sidebar", ".recommended-vehicles",
                    "script", "style", ".ads", ".advertisement"
                ],
                "keep_only_main_content": True,
                "remove_duplicate_text": True
            },
            "extraction_order": [
                "vehicle_heading",
                "stock_number",
                "vin",
                "price_section",
                "description",
                "features",
                "disclaimers"
            ]
        }
        self._save_template(dealer_com)

        # Generic fallback template
        generic = {
            "template_id": "generic_fallback",
            "platform": "unknown",
            "selectors": {
                "vehicle_heading": "h1, .title, .vehicle-title",
                "price_primary": ".price, .pricing, [class*='price']",
                "description": ".description, .details, main"
            },
            "cleanup_rules": {
                "remove_selectors": ["nav", "header", "footer", "script", "style"],
                "keep_only_main_content": False
            },
            "extraction_order": ["vehicle_heading", "price_primary", "description"]
        }
        self._save_template(generic)

    def _save_template(self, config: Dict):
        """Save template to database."""
        template_id = config['template_id']
        platform = config['platform']
        selectors = config.get('selectors', {})
        cleanup_rules = config.get('cleanup_rules', {})
        extraction_order = config.get('extraction_order', [])

        self.db.save_extraction_template(
            template_id=template_id,
            platform=platform,
            selectors=selectors,
            cleanup_rules=cleanup_rules,
            extraction_order=extraction_order
        )
        logger.info(f"Saved extraction template: {template_id}")

    def get_template(
        self,
        url: str,
        platform: str = None,
        template_override: str = None
    ) -> ExtractionTemplate:
        """
        Get extraction template using override hierarchy.

        Priority:
        1. template_override (explicit)
        2. URL-specific template
        3. Platform template
        4. Generic fallback

        Args:
            url: Page URL
            platform: Detected platform
            template_override: Explicit template ID

        Returns:
            ExtractionTemplate instance
        """
        # 1. Explicit override
        if template_override:
            config = self._load_template(template_override)
            if config:
                logger.info(f"Using override template: {template_override}")
                return ExtractionTemplate(config)

        # 2. URL-specific template
        domain = urlparse(url).netloc.replace('www.', '')
        url_template_id = f"url_{domain.replace('.', '_')}"
        config = self._load_template(url_template_id)
        if config:
            logger.info(f"Using URL-specific template: {url_template_id}")
            return ExtractionTemplate(config)

        # 3. Platform template
        if platform and platform != "unknown":
            platform_template_id = f"{platform.lower().replace(' ', '_')}_vdp"
            config = self._load_template(platform_template_id)
            if config:
                logger.info(f"Using platform template: {platform_template_id}")
                return ExtractionTemplate(config)

        # 4. Generic fallback
        logger.info("Using generic fallback template")
        config = self._load_template("generic_fallback")
        return ExtractionTemplate(config)

    def _load_template(self, template_id: str) -> Optional[Dict]:
        """Load template from database."""
        template_data = self.db.get_extraction_template(template_id)
        if not template_data:
            return None

        return {
            'template_id': template_data['template_id'],
            'platform': template_data['platform'],
            'selectors': template_data['selectors'],
            'cleanup_rules': template_data['cleanup_rules'],
            'extraction_order': template_data['extraction_order']
        }

    def create_url_override(
        self,
        url: str,
        selectors: Dict[str, str],
        cleanup_rules: Dict = None
    ):
        """
        Create a URL-specific template override.

        Args:
            url: URL to override
            selectors: Custom selectors
            cleanup_rules: Custom cleanup rules
        """
        domain = urlparse(url).netloc.replace('www.', '')
        template_id = f"url_{domain.replace('.', '_')}"

        config = {
            "template_id": template_id,
            "platform": "custom",
            "url_pattern": url,
            "selectors": selectors,
            "cleanup_rules": cleanup_rules or {},
            "extraction_order": list(selectors.keys())
        }

        self._save_template(config)
        logger.info(f"Created URL override: {template_id} for {url}")


def main():
    """Example usage."""
    import asyncio
    from playwright.async_api import async_playwright

    async def demo():
        manager = ExtractionTemplateManager()

        # Get template for dealer.com URL
        url = "https://www.allstarcdjrmuskogee.com/used/Chevrolet/2022-Chevrolet-Silverado-1500-f793dc61ac184236e10863afe4bf9621.htm"
        template = manager.get_template(url, platform="dealer.com")

        # Extract content
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url)

            extracted = await template.extract(page)

            print("\n=== EXTRACTED CONTENT ===")
            for section, content in extracted.items():
                print(f"\n{section.upper()}:")
                print(content[:200] + "..." if len(content) > 200 else content)

            await browser.close()

    asyncio.run(demo())


if __name__ == "__main__":
    main()
