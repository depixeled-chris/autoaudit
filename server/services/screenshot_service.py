"""Screenshot service for capturing project previews."""

import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging
from playwright.async_api import async_playwright
import sys
from pathlib import Path as PathLib

sys.path.insert(0, str(PathLib(__file__).parent.parent))

from core.database import ComplianceDatabase
from core.config import DATABASE_PATH

logger = logging.getLogger(__name__)


class ScreenshotService:
    """Service for capturing project screenshots."""

    def __init__(self, db: ComplianceDatabase):
        self.db = db
        self.screenshots_dir = Path("screenshots/projects")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    async def capture_project_screenshot(
        self,
        project_id: int,
        url: str,
        width: int = 1280,
        height: int = 720
    ) -> Optional[str]:
        """
        Capture a screenshot of a project's base URL.

        Args:
            project_id: Project ID
            url: URL to screenshot
            width: Viewport width
            height: Viewport height

        Returns:
            Path to saved screenshot relative to server root, or None if failed
        """
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"project_{project_id}_{timestamp}.png"
            screenshot_path = self.screenshots_dir / filename

            # Capture screenshot using Playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(viewport={"width": width, "height": height})

                try:
                    # Navigate with less strict wait condition and longer timeout
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)

                    # Wait a bit for initial content to render
                    await page.wait_for_timeout(2000)

                    # Capture screenshot
                    await page.screenshot(path=str(screenshot_path), full_page=False)
                    logger.info(f"Screenshot captured: {screenshot_path}")
                except Exception as e:
                    logger.error(f"Failed to capture screenshot for {url}: {e}")
                    await browser.close()
                    return None

                await browser.close()

            # Update database with screenshot path (relative to screenshots mount point)
            # FastAPI mounts /app/screenshots at /screenshots
            # So path should be "projects/project_1_timestamp.png" (without "screenshots/" prefix)
            # Frontend will access as: http://localhost:8000/screenshots/projects/project_1_timestamp.png
            relative_path = f"screenshots/projects/{filename}"
            self.db.update_project_screenshot(project_id, relative_path)

            return relative_path

        except Exception as e:
            logger.error(f"Screenshot service error: {e}")
            return None


def capture_screenshot_sync(project_id: int, url: str) -> Optional[str]:
    """
    Synchronous wrapper for screenshot capture.

    Args:
        project_id: Project ID
        url: URL to screenshot

    Returns:
        Path to screenshot or None
    """
    db = ComplianceDatabase(DATABASE_PATH)
    try:
        service = ScreenshotService(db)
        return asyncio.run(service.capture_project_screenshot(project_id, url))
    finally:
        db.close()
