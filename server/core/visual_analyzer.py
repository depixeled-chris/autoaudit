"""Visual compliance analysis using screenshots and GPT-4V."""

import os
import base64
from typing import Dict, Optional
from openai import AsyncOpenAI
import logging
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VisualComplianceAnalyzer:
    """Analyzes webpage screenshots for visual compliance."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the visual analyzer.

        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found.")

        self.client = AsyncOpenAI(api_key=self.api_key)
        logger.info("VisualComplianceAnalyzer initialized")

    async def verify_visual_compliance(
        self,
        screenshot_path: str,
        rule_to_verify: str,
        context: Dict[str, str]
    ) -> Dict:
        """
        Verify a specific compliance rule using visual analysis.

        Args:
            screenshot_path: Path to screenshot file
            rule_to_verify: The specific rule being verified
            context: Additional context (URL, state, etc.)

        Returns:
            Dictionary with verification results
        """
        logger.info(f"Visual verification for: {rule_to_verify}")

        # Read and encode screenshot
        with open(screenshot_path, "rb") as f:
            screenshot_b64 = base64.b64encode(f.read()).decode('utf-8')

        # Build verification prompt
        prompt = self._build_visual_prompt(rule_to_verify, context)

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",  # GPT-4V
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screenshot_b64}"
                                }
                            }
                        ]
                    }
                ],
                max_completion_tokens=1000,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            import json
            result = json.loads(result_text)

            result["tokens_used"] = response.usage.total_tokens
            result["verification_method"] = "visual"

            logger.info(f"Visual verification complete. Compliant: {result.get('is_compliant')}")
            return result

        except Exception as e:
            logger.error(f"Error during visual verification: {str(e)}")
            raise

    def _build_visual_prompt(self, rule: str, context: Dict[str, str]) -> str:
        """Build the prompt for visual analysis."""

        prompt = f"""You are analyzing a screenshot of an auto dealership webpage to verify visual compliance.

**Rule to Verify:**
{rule}

**Context:**
- URL: {context.get('url', 'N/A')}
- State: {context.get('state', 'N/A')}

**Your Task:**
Look at the screenshot and determine if the rule is visually compliant. Focus on:
- Spatial positioning and proximity
- Visual hierarchy (font size, placement, prominence)
- Whether a typical consumer would easily see the required information
- Actual layout as rendered, not theoretical placement

**Analysis Framework:**
1. **Locate the relevant elements** (price, vehicle info, disclaimers, etc.)
2. **Measure visual proximity** - Are they in the same visual section/card?
3. **Assess conspicuousness** - Is information reasonably visible and readable?
4. **Consider user experience** - Would a consumer naturally see this?

**Respond in JSON format:**
{{
    "is_compliant": true/false,
    "confidence": 0.0-1.0,
    "visual_evidence": "Description of what you see in the screenshot",
    "proximity_description": "How close are the relevant elements? Same card? How many pixels apart?",
    "recommendation": "If non-compliant, what needs to change?",
    "reasoning": "Detailed explanation of your determination"
}}

**Important:**
- Be practical, not pedantic
- Focus on consumer experience
- Consider if information is reasonably accessible
- Give credit for good-faith compliance efforts
"""
        return prompt

    async def capture_and_verify(
        self,
        page,
        rule: str,
        context: Dict[str, str],
        output_dir: str = "screenshots"
    ) -> Dict:
        """
        Capture screenshot and verify compliance in one step.

        Args:
            page: Playwright page object
            rule: Rule to verify
            context: Context dictionary
            output_dir: Directory to save screenshots

        Returns:
            Verification result
        """
        Path(output_dir).mkdir(exist_ok=True)

        # Generate filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        url_slug = context.get('url', '').replace('https://', '').replace('http://', '').replace('/', '_')[:50]
        screenshot_path = Path(output_dir) / f"visual_{url_slug}_{timestamp}.png"

        # Capture screenshot
        await page.screenshot(path=str(screenshot_path), full_page=True)
        logger.info(f"Screenshot saved: {screenshot_path}")

        # Verify
        result = await self.verify_visual_compliance(
            screenshot_path=str(screenshot_path),
            rule_to_verify=rule,
            context=context
        )

        result["screenshot_path"] = str(screenshot_path)
        return result


async def main():
    """Example usage."""
    from playwright.async_api import async_playwright

    analyzer = VisualComplianceAnalyzer()

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://example.com")

        result = await analyzer.capture_and_verify(
            page=page,
            rule="Vehicle identification (year, make, model) must be conspicuously disclosed adjacent to price",
            context={"url": "https://example.com", "state": "Oklahoma"}
        )

        print(result)
        await browser.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
