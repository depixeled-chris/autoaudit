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
        from core.database import ComplianceDatabase
        self.db = ComplianceDatabase(db_path)
        self._load_default_templates()
        logger.info(f"ExtractionTemplateManager initialized with database: {db_path}")

    def _load_default_templates(self):
        """Load default templates for common platforms and URL types."""

        # VDP (Vehicle Detail Page) - Aggressive cleanup, focus on vehicle only
        vdp_template = {
            "template_id": "vdp_default",
            "platform": "vdp",
            "selectors": {
                "vehicle_heading": ".vehicle-title h1, .vdp-title h1, h1.vehicle-name, h1",
                "price_primary": ".pricing-module .price, .internet-price, .final-price, [class*='price']",
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
                    "script", "style", ".ads", ".advertisement", ".chat-widget"
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
        self._save_template(vdp_template)

        # Dealer.com VDP (specific platform)
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

        # HOMEPAGE - Minimal cleanup, preserve ALL contact info
        homepage = {
            "template_id": "homepage_default",
            "platform": "homepage",
            "selectors": {
                "dealership_name": "h1, .dealership-name, .dealer-name, .brand-name",
                "header_contact": "header [class*='phone'], header [class*='contact'], .header-phone",
                "main_content": "main, .main-content, #main, .content",
                "footer_content": "footer, .footer, .site-footer, #footer",
                "contact_section": ".contact, .contact-us, .location, .hours",
                "promotional_banners": ".banner, .promo, .special, .hero",
                "featured_vehicles": ".featured, .inventory-preview, .vehicle-showcase"
            },
            "cleanup_rules": {
                "remove_selectors": [
                    "script", "style", ".ads", ".advertisement",
                    "iframe[src*='chat']", ".chat-widget"
                ],
                "keep_only_main_content": False,  # CRITICAL: Keep full page including footer
                "remove_duplicate_text": False  # Don't remove duplicates - footer might repeat header info
            },
            "extraction_order": [
                "dealership_name",
                "header_contact",
                "main_content",
                "promotional_banners",
                "featured_vehicles",
                "contact_section",
                "footer_content"
            ]
        }
        self._save_template(homepage)

        # INVENTORY - Moderate cleanup, keep structure for filtering/sorting
        inventory = {
            "template_id": "inventory_default",
            "platform": "inventory",
            "selectors": {
                "page_heading": "h1, .page-title, .inventory-title",
                "filter_section": ".filters, .search-filters, .inventory-filters",
                "vehicle_cards": ".vehicle-card, .inventory-item, .vehicle-listing",
                "general_disclaimers": ".inventory-disclaimer, .general-disclaimer, footer .disclaimer",
                "pagination": ".pagination, .page-nav",
                "sort_controls": ".sort, .sorting, [class*='sort']"
            },
            "cleanup_rules": {
                "remove_selectors": [
                    ".site-header nav", ".main-navigation", ".mega-menu",
                    "script", "style", ".ads", ".advertisement", ".chat-widget",
                    ".recommended-vehicles", ".recent-searches"
                ],
                "keep_only_main_content": False,  # Keep some structure
                "remove_duplicate_text": True
            },
            "extraction_order": [
                "page_heading",
                "filter_section",
                "sort_controls",
                "vehicle_cards",
                "pagination",
                "general_disclaimers"
            ]
        }
        self._save_template(inventory)

        # SPECIALS - Light cleanup, preserve terms/conditions
        specials = {
            "template_id": "specials_default",
            "platform": "specials",
            "selectors": {
                "page_heading": "h1, .page-title, .specials-title",
                "promotional_offers": ".special, .promo, .offer, .deal",
                "terms_conditions": ".terms, .conditions, .disclaimer, .fine-print",
                "expiration_dates": "[class*='expir'], [class*='valid-through']",
                "footer_disclaimers": "footer .disclaimer, footer .terms"
            },
            "cleanup_rules": {
                "remove_selectors": [
                    "script", "style", ".ads", ".advertisement", ".chat-widget"
                ],
                "keep_only_main_content": False,  # Keep footer for disclaimers
                "remove_duplicate_text": False  # Terms might be repeated
            },
            "extraction_order": [
                "page_heading",
                "promotional_offers",
                "expiration_dates",
                "terms_conditions",
                "footer_disclaimers"
            ]
        }
        self._save_template(specials)

        # SERVICE - Light cleanup, preserve hours/location
        service = {
            "template_id": "service_default",
            "platform": "service",
            "selectors": {
                "service_heading": "h1, .service-title, .page-title",
                "service_hours": ".hours, .service-hours, [class*='hour']",
                "location_info": ".location, .address, .contact",
                "service_offerings": ".services, .service-list, .offerings",
                "pricing_specials": ".service-special, .coupon, .service-price",
                "footer_contact": "footer .contact, footer .hours"
            },
            "cleanup_rules": {
                "remove_selectors": [
                    "script", "style", ".ads", ".advertisement", ".chat-widget"
                ],
                "keep_only_main_content": False,  # Keep footer for hours/contact
                "remove_duplicate_text": False
            },
            "extraction_order": [
                "service_heading",
                "service_hours",
                "location_info",
                "service_offerings",
                "pricing_specials",
                "footer_contact"
            ]
        }
        self._save_template(service)

        # FINANCING - Light cleanup, preserve legal disclaimers
        financing = {
            "template_id": "financing_default",
            "platform": "financing",
            "selectors": {
                "financing_heading": "h1, .financing-title, .page-title",
                "rate_information": ".rates, .apr, .financing-rates",
                "calculator": ".calculator, .payment-calculator",
                "disclaimers": ".disclaimer, .disclosure, .legal",
                "footer_legal": "footer .disclaimer, footer .legal, footer .disclosure"
            },
            "cleanup_rules": {
                "remove_selectors": [
                    "script", "style", ".ads", ".advertisement", ".chat-widget"
                ],
                "keep_only_main_content": False,  # Keep footer for legal text
                "remove_duplicate_text": False  # Legal text might be repeated
            },
            "extraction_order": [
                "financing_heading",
                "rate_information",
                "calculator",
                "disclaimers",
                "footer_legal"
            ]
        }
        self._save_template(financing)

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
                "remove_selectors": ["script", "style"],  # Don't remove structural elements
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
        template_override: str = None,
        url_type: str = "VDP"
    ) -> ExtractionTemplate:
        """
        Get extraction template using override hierarchy.

        Priority:
        1. template_override (explicit)
        2. URL-specific template
        3. URL type template (VDP, HOMEPAGE, INVENTORY, etc.)
        4. Platform template
        5. Generic fallback

        Args:
            url: Page URL
            platform: Detected platform
            template_override: Explicit template ID
            url_type: Type of URL (VDP, HOMEPAGE, INVENTORY, SPECIALS, SERVICE, FINANCING)

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

        # 3. URL type template (NEW - primary selection method)
        if url_type:
            url_type_lower = url_type.lower()
            type_template_id = f"{url_type_lower}_default"
            config = self._load_template(type_template_id)
            if config:
                logger.info(f"Using URL type template: {type_template_id} (type={url_type})")
                return ExtractionTemplate(config)

        # 4. Platform template
        if platform and platform != "unknown":
            platform_template_id = f"{platform.lower().replace(' ', '_')}_vdp"
            config = self._load_template(platform_template_id)
            if config:
                logger.info(f"Using platform template: {platform_template_id}")
                return ExtractionTemplate(config)

        # 5. Generic fallback
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
