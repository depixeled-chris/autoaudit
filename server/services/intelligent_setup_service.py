"""Intelligent project setup service using LLM to analyze dealership websites."""

import sys
from pathlib import Path
from typing import Dict, Optional, List
import logging
import re
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scraper import DealershipScraper
from core.converter import ContentConverter
from core.analyzer import ComplianceAnalyzer
from core.database import ComplianceDatabase
from schemas.project import ProjectCreate, ProjectResponse, IntelligentSetupResponse
from schemas.url import URLCreate
from services.project_service import ProjectService
from services.screenshot_service import ScreenshotService
from services.base_service import BaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntelligentSetupService(BaseService):
    """Service for intelligent project setup from a single URL."""

    def __init__(self, db):
        """Initialize service with database and analyzer."""
        super().__init__(db)
        self.analyzer = None  # Lazy initialization

    async def setup_from_url(self, starting_url: str) -> IntelligentSetupResponse:
        """
        Analyze a dealership website and create a project with monitoring URLs.

        Args:
            starting_url: Any URL from the dealership website

        Returns:
            IntelligentSetupResponse with created project and URLs

        Raises:
            ValueError: If analysis or setup fails
        """
        logger.info(f"Starting intelligent setup for: {starting_url}")

        try:
            # Step 1: Scrape the starting page
            async with DealershipScraper() as scraper:
                page_data = await scraper.scrape_page(starting_url)

            # Step 2: Extract base information from page
            platform = page_data['platform']
            base_url = self._extract_base_url(starting_url)

            # Step 3: Convert to markdown for LLM analysis
            converter = ContentConverter()
            markdown = converter.html_to_markdown(page_data['html'])

            # Step 4: Use LLM to analyze the page and extract dealership info
            analysis_result = await self._analyze_dealership(
                markdown=markdown,
                url=starting_url,
                platform=platform
            )

            # Validate that the state has rules configured
            state_code = analysis_result['state_code']
            cursor = self.db.conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM rules WHERE state_code = ? AND active = 1",
                (state_code,)
            )
            active_rules_count = cursor.fetchone()[0]

            if active_rules_count == 0:
                raise ValueError(
                    f"State {state_code} has no active compliance rules configured. "
                    "Please go to Config → States to upload legislation and generate rules first."
                )

            # Step 5: Create the project
            project_service = ProjectService(self.db)

            # Handle duplicate names by appending a number
            project_name = analysis_result['dealership_name']
            name_suffix = 1
            while True:
                try:
                    project_data = ProjectCreate(
                        name=project_name,
                        state_code=analysis_result['state_code'],
                        description=f"Auto-detected dealership ({platform} platform)" if platform != 'unknown' else "Auto-detected dealership",
                        base_url=base_url
                    )
                    project = project_service.create_project(project_data)
                    break
                except ValueError as e:
                    if "UNIQUE constraint failed" in str(e) or "already exists" in str(e).lower():
                        project_name = f"{analysis_result['dealership_name']} ({name_suffix})"
                        name_suffix += 1
                        if name_suffix > 10:  # Prevent infinite loop
                            raise ValueError(f"Too many projects with similar names: {analysis_result['dealership_name']}")
                    else:
                        raise

            # Step 6: Create URLs with appropriate frequencies
            page_urls = analysis_result.get('page_urls', {})
            urls_created = await self._create_monitoring_urls(
                project_id=project.id,
                base_url=base_url,
                page_urls=page_urls,
                platform=platform
            )

            # Step 7: Capture screenshot
            try:
                screenshot_service = ScreenshotService(self.db)
                await screenshot_service.capture_project_screenshot(
                    project_id=project.id,
                    url=base_url
                )
                logger.info(f"Captured screenshot for project {project.id}")
                # Refresh project to get updated screenshot_path
                refreshed_project = project_service.get_project(project.id)
                if refreshed_project:
                    project = refreshed_project
            except Exception as e:
                logger.warning(f"Failed to capture screenshot: {str(e)}")
                # Continue even if screenshot fails

            # Step 8: Build summary
            summary = self._build_summary(
                dealership_name=analysis_result['dealership_name'],
                state_code=analysis_result['state_code'],
                platform=platform,
                urls_created=urls_created
            )

            logger.info(f"Intelligent setup complete: {summary}")

            return IntelligentSetupResponse(
                project=project,
                urls_created=len(urls_created),
                analysis_summary=summary
            )

        except Exception as e:
            logger.error(f"Intelligent setup failed: {str(e)}")
            raise ValueError(f"Failed to set up project: {str(e)}")

    async def _analyze_dealership(
        self,
        markdown: str,
        url: str,
        platform: str
    ) -> Dict:
        """
        Use LLM to analyze the dealership page and extract key information.

        Args:
            markdown: Markdown content of the page
            url: Original URL
            platform: Detected platform

        Returns:
            Dictionary with dealership_name, state_code, homepage_url, inventory_url, etc.
        """
        # Lazy initialize analyzer
        if self.analyzer is None:
            try:
                self.analyzer = ComplianceAnalyzer()
            except Exception as e:
                logger.error(f"Failed to initialize ComplianceAnalyzer: {str(e)}")
                raise

        prompt = f"""Analyze this dealership website to extract key information and identify all major page types.

URL: {url}
Detected Platform: {platform}

# Page Content

{markdown[:10000]}  # Limit content to avoid token limits

# Task

Extract dealership information and identify URLs for different page types:

1. **Dealership Name**: The official name of the dealership
2. **State Code**: Two-letter US state code (e.g., OK, CA, TX, NY)
3. **Page URLs**: Find links to the following page types (set to null if not found):
   - homepage: Main homepage/landing page
   - new_inventory: New vehicle inventory listing
   - used_inventory: Used vehicle inventory listing
   - inventory: General inventory page (if new/used not separated)
   - specials: Special offers/promotions page
   - financing: Finance/payment calculator page
   - lease: Lease calculator/offers page
   - service: Service department page
   - parts: Parts department page
   - cpo: Certified pre-owned inventory
   - trade_in: Trade-in value calculator
   - contact: Contact us page

Respond in JSON format:

{{
    "dealership_name": "<name>",
    "state_code": "<XX>",
    "page_urls": {{
        "homepage": "<url or null>",
        "new_inventory": "<url or null>",
        "used_inventory": "<url or null>",
        "inventory": "<url or null>",
        "specials": "<url or null>",
        "financing": "<url or null>",
        "lease": "<url or null>",
        "service": "<url or null>",
        "parts": "<url or null>",
        "cpo": "<url or null>",
        "trade_in": "<url or null>",
        "contact": "<url or null>"
    }},
    "confidence": {{
        "dealership_name": <0.0-1.0>,
        "state_code": <0.0-1.0>
    }},
    "reasoning": "<brief explanation of how you determined these values>"
}}

**Important**:
- Only include URLs you can confidently identify from navigation links or page content
- State code must be a valid 2-letter US state code
- URLs should be complete (starting with http:// or https://)
- If a dealership doesn't separate new/used inventory, use the general "inventory" URL
"""

        try:
            # Use the existing analyzer client to make the API call
            response = await self.analyzer.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing dealership websites and extracting structured information."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_completion_tokens=1000,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            if not result_text:
                raise ValueError("Empty response from LLM")

            result = json.loads(result_text)
            logger.info(f"LLM analysis result: {result}")

            # Validate and fill in defaults
            if not result.get('dealership_name'):
                result['dealership_name'] = self._extract_name_from_url(url)

            if not result.get('state_code') or len(result['state_code']) != 2:
                result['state_code'] = 'CA'  # Default to CA if not detected

            result['state_code'] = result['state_code'].upper()

            return result

        except Exception as e:
            logger.error(f"LLM analysis failed: {str(e)}")
            # Fallback to basic extraction
            return {
                "dealership_name": self._extract_name_from_url(url),
                "state_code": "CA",  # Default
                "homepage_url": None,
                "inventory_url": None,
                "confidence": {
                    "dealership_name": 0.3,
                    "state_code": 0.1,
                    "inventory_url": 0.0
                },
                "reasoning": f"LLM analysis failed, using fallback extraction: {str(e)}"
            }

    async def _find_sample_vdp(self, inventory_url: str, platform: str) -> Optional[str]:
        """
        Scrape the inventory page to find a sample VDP URL.

        Args:
            inventory_url: URL of the inventory page
            platform: Detected platform

        Returns:
            Sample VDP URL or None if not found
        """
        try:
            async with DealershipScraper() as scraper:
                inventory_data = await scraper.scrape_page(inventory_url)

            # Extract all links from the page
            html = inventory_data['html']

            # Common VDP URL patterns by platform
            vdp_patterns = {
                'dealer.com': r'href="([^"]*/(new|used)/[^"]*\.htm[^"]*)"',
                'DealerOn': r'href="([^"]*/(vehicle|inventory)/[^"]*)"',
                'unknown': r'href="([^"]*/(?:new|used|vehicle|inventory)/[^"]*)"'
            }

            pattern = vdp_patterns.get(platform, vdp_patterns['unknown'])
            matches = re.findall(pattern, html, re.IGNORECASE)

            if matches:
                # Get the first match (it's a tuple from the regex groups)
                vdp_path = matches[0][0] if isinstance(matches[0], tuple) else matches[0]

                # Make it absolute if it's relative
                if vdp_path.startswith('http'):
                    return vdp_path
                elif vdp_path.startswith('/'):
                    base_url = self._extract_base_url(inventory_url)
                    return f"{base_url}{vdp_path}"
                else:
                    return None

            logger.warning(f"No VDP URLs found on inventory page: {inventory_url}")
            return None

        except Exception as e:
            logger.error(f"Failed to find sample VDP: {str(e)}")
            return None

    async def _create_monitoring_urls(
        self,
        project_id: int,
        base_url: str,
        page_urls: Dict[str, Optional[str]],
        platform: str
    ) -> List[Dict]:
        """
        Create monitoring URLs with appropriate frequencies.

        Args:
            project_id: Project ID
            base_url: Base URL of the dealership
            page_urls: Dictionary of page_type -> URL mappings
            platform: Detected platform

        Returns:
            List of created URL records
        """
        created_urls = []

        # Define check frequencies for each page type (in hours)
        # Key pages checked more frequently, static pages less frequently
        frequency_map = {
            'homepage': 24,          # Daily
            'new_inventory': 168,    # Weekly
            'used_inventory': 168,   # Weekly
            'inventory': 168,        # Weekly
            'specials': 48,          # Every 2 days (promotions change frequently)
            'financing': 168,        # Weekly
            'lease': 168,            # Weekly
            'service': 720,          # Monthly
            'parts': 720,            # Monthly
            'cpo': 168,              # Weekly
            'trade_in': 720,         # Monthly
            'contact': 8760,         # Yearly (rarely changes)
        }

        # Always create homepage
        homepage = page_urls.get('homepage') or base_url
        url_id = self.db.add_url(
            url=homepage,
            project_id=project_id,
            url_type="HOMEPAGE",
            platform=platform if platform != 'unknown' else None,
            check_frequency_hours=frequency_map['homepage']
        )
        created_urls.append(self.db.get_url(url_id=url_id))
        logger.info(f"Created HOMEPAGE URL: {homepage}")

        # Create URLs for each detected page type
        page_type_mapping = {
            'new_inventory': 'NEW_INVENTORY',
            'used_inventory': 'USED_INVENTORY',
            'inventory': 'INVENTORY',
            'specials': 'SPECIALS',
            'financing': 'FINANCING',
            'lease': 'LEASE',
            'service': 'SERVICE',
            'parts': 'PARTS',
            'cpo': 'CPO',
            'trade_in': 'TRADE_IN',
            'contact': 'CONTACT',
        }

        for key, url_type_code in page_type_mapping.items():
            url = page_urls.get(key)
            if url:
                try:
                    url_id = self.db.add_url(
                        url=url,
                        project_id=project_id,
                        url_type=url_type_code,
                        platform=platform if platform != 'unknown' else None,
                        check_frequency_hours=frequency_map.get(key, 720)
                    )
                    created_urls.append(self.db.get_url(url_id=url_id))
                    logger.info(f"Created {url_type_code} URL: {url}")
                except Exception as e:
                    logger.warning(f"Failed to create {url_type_code} URL: {str(e)}")

        # Try to find a sample VDP from inventory pages if not explicitly found
        sample_vdp_url = None
        for inv_key in ['new_inventory', 'used_inventory', 'inventory']:
            inv_url = page_urls.get(inv_key)
            if inv_url:
                sample_vdp_url = await self._find_sample_vdp(inv_url, platform)
                if sample_vdp_url:
                    break

        # Sample VDP: scrape once only (9999 hours = effectively once)
        if sample_vdp_url:
            try:
                url_id = self.db.add_url(
                    url=sample_vdp_url,
                    project_id=project_id,
                    url_type="VDP",
                    platform=platform if platform != 'unknown' else None,
                    check_frequency_hours=9999  # Effectively once-only
                )
                created_urls.append(self.db.get_url(url_id=url_id))
                logger.info(f"Created VDP URL: {sample_vdp_url}")
            except Exception as e:
                logger.warning(f"Failed to create VDP URL: {str(e)}")

        return created_urls

    def _extract_base_url(self, url: str) -> str:
        """Extract base URL (scheme + domain) from a full URL."""
        match = re.match(r'(https?://[^/]+)', url)
        if match:
            return match.group(1)
        return url

    def _extract_name_from_url(self, url: str) -> str:
        """Extract a dealership name from URL as fallback."""
        # Remove protocol and www
        name = re.sub(r'https?://(www\.)?', '', url)
        # Take the domain name before the first slash or dot after the main part
        name = name.split('/')[0].split('.')[0]
        # Convert to title case and replace hyphens/underscores
        name = name.replace('-', ' ').replace('_', ' ').title()
        return name

    def _build_summary(
        self,
        dealership_name: str,
        state_code: str,
        platform: str,
        urls_created: List[Dict]
    ) -> str:
        """Build a summary of the setup process."""
        # Filter out None values and extract url_types
        url_types = [url['url_type'] for url in urls_created if url is not None]

        parts = [f"Detected {dealership_name} dealership in {state_code}."]

        if platform != 'unknown':
            parts.append(f"Platform: {platform}.")

        url_desc = []
        if 'homepage' in url_types:
            url_desc.append('homepage')
        if 'inventory' in url_types:
            url_desc.append('inventory page')
        if 'vdp' in url_types:
            url_desc.append('sample VDP')

        if url_desc:
            parts.append(f"Created monitoring for {', '.join(url_desc)}.")

        return ' '.join(parts)
