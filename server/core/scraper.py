"""Web scraping module using Playwright for dealership websites."""

import asyncio
from typing import Optional, Dict
from playwright.async_api import async_playwright, Browser, Page
import logging

from .config import SCRAPING_TIMEOUT, USER_AGENT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DealershipScraper:
    """Scrapes auto dealership websites with JavaScript rendering support."""

    def __init__(self):
        self.browser: Optional[Browser] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def start(self):
        """Initialize the browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        logger.info("Browser initialized")

    async def close(self):
        """Close the browser."""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        logger.info("Browser closed")

    async def scrape_page(self, url: str) -> Dict[str, str]:
        """
        Scrape a dealership webpage.

        Args:
            url: The URL to scrape

        Returns:
            Dictionary containing HTML content and metadata
        """
        if not self.browser:
            raise RuntimeError("Browser not initialized. Use async context manager.")

        logger.info(f"Scraping: {url}")

        page: Page = await self.browser.new_page(user_agent=USER_AGENT)

        try:
            # Navigate to the page
            await page.goto(url, wait_until="domcontentloaded", timeout=SCRAPING_TIMEOUT)

            # Wait for main content to load (adjust selector as needed)
            try:
                await page.wait_for_selector("body", timeout=5000)
            except:
                logger.warning("Body selector timeout, continuing anyway")

            # Extract content
            html_content = await page.content()
            title = await page.title()

            # Get text content for quick analysis
            body_text = await page.evaluate("() => document.body.innerText")

            # Try to detect common dealership platforms
            platform = await self._detect_platform(page)

            return {
                "url": url,
                "html": html_content,
                "title": title,
                "body_text": body_text,
                "platform": platform,
            }

        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            raise
        finally:
            await page.close()

    async def _detect_platform(self, page: Page) -> str:
        """
        Detect the dealership website platform.

        Args:
            page: Playwright page object

        Returns:
            Platform name or 'unknown'
        """
        # Check for common dealership platforms
        platforms = {
            "dealer.com": ["dealer-logo", "vdp-container"],
            "DealerOn": ["dealeron", "dealer-on"],
            "AutoTrader": ["atc-", "autotrader"],
            "Cars.com": ["cars-com", "listing-container"],
            "CDK": ["cdk-", "adf-"],
        }

        for platform_name, selectors in platforms.items():
            for selector in selectors:
                try:
                    element = await page.query_selector(f"[class*='{selector}']")
                    if element:
                        return platform_name
                except:
                    continue

        return "unknown"

    async def scrape_multiple(self, urls: list[str]) -> list[Dict[str, str]]:
        """
        Scrape multiple URLs concurrently.

        Args:
            urls: List of URLs to scrape

        Returns:
            List of scraped data dictionaries
        """
        tasks = [self.scrape_page(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to scrape {urls[i]}: {result}")
            else:
                valid_results.append(result)

        return valid_results


async def main():
    """Example usage."""
    test_url = "https://www.example-dealership.com"

    async with DealershipScraper() as scraper:
        data = await scraper.scrape_page(test_url)
        print(f"Scraped: {data['title']}")
        print(f"Platform: {data['platform']}")
        print(f"Content length: {len(data['html'])} characters")


if __name__ == "__main__":
    asyncio.run(main())
