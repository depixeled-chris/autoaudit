"""Main orchestration script for auto dealership compliance checking."""

import asyncio
import argparse
import sys
import logging
from typing import Optional

from scraper import DealershipScraper
from converter import ContentConverter
from analyzer import ComplianceAnalyzer
from reporter import ComplianceReporter
from config import STATE_REGULATIONS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComplianceChecker:
    """Main orchestrator for the compliance checking pipeline."""

    def __init__(self, state_code: str, output_dir: str = "reports"):
        """
        Initialize the compliance checker.

        Args:
            state_code: Two-letter state code (e.g., 'CA', 'TX', 'NY')
            output_dir: Directory to save reports
        """
        if state_code not in STATE_REGULATIONS:
            raise ValueError(f"State '{state_code}' not supported. Available: {list(STATE_REGULATIONS.keys())}")

        self.state_code = state_code
        self.state_rules = STATE_REGULATIONS[state_code]
        self.converter = ContentConverter()
        self.analyzer = ComplianceAnalyzer()
        self.reporter = ComplianceReporter(output_dir)

        logger.info(f"ComplianceChecker initialized for {self.state_rules.state}")

    async def check_url(self, url: str, save_formats: list = ["markdown"]) -> dict:
        """
        Check a single URL for compliance.

        Args:
            url: Dealership website URL
            save_formats: List of report formats to save (markdown, json, html)

        Returns:
            Analysis results dictionary
        """
        logger.info(f"Starting compliance check for: {url}")

        try:
            # Step 1: Scrape the website
            logger.info("Step 1/4: Scraping website...")
            async with DealershipScraper() as scraper:
                scraped_data = await scraper.scrape_page(url)

            logger.info(f"✓ Scraped successfully. Platform: {scraped_data['platform']}")

            # Step 2: Convert to Markdown
            logger.info("Step 2/4: Converting to Markdown...")
            markdown = self.converter.html_to_markdown(scraped_data['html'])
            sections = self.converter.extract_sections(markdown, scraped_data)
            llm_input = self.converter.prepare_for_llm(sections)

            logger.info(f"✓ Converted to Markdown ({len(llm_input)} characters)")

            # Save the LLM input for review
            from datetime import datetime
            from pathlib import Path

            input_dir = Path("llm_inputs")
            input_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            url_slug = url.replace('https://', '').replace('http://', '').replace('/', '_')[:50]
            input_filename = input_dir / f"llm_input_{url_slug}_{timestamp}.md"

            with open(input_filename, 'w', encoding='utf-8') as f:
                f.write(f"# LLM Input for Compliance Analysis\n\n")
                f.write(f"**URL:** {url}\n")
                f.write(f"**State:** {self.state_rules.state}\n")
                f.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Character Count:** {len(llm_input)}\n\n")
                f.write("---\n\n")
                f.write(llm_input)

            logger.info(f"✓ LLM input saved to: {input_filename}")

            # Step 3: Analyze compliance
            logger.info("Step 3/4: Analyzing compliance with LLM...")
            analysis_result = await self.analyzer.analyze_compliance(
                content=llm_input,
                state_rules=self.state_rules,
                url=url
            )

            logger.info(f"✓ Analysis complete. Score: {analysis_result.get('overall_compliance_score', 0)}/100")

            # Step 4: Generate reports
            logger.info("Step 4/4: Generating reports...")
            saved_reports = {}
            for format in save_formats:
                report_path = self.reporter.save_report(analysis_result, format=format)
                saved_reports[format] = report_path

            logger.info(f"✓ Reports saved: {', '.join(saved_reports.values())}")

            # Add report paths to result
            analysis_result['report_paths'] = saved_reports

            return analysis_result

        except Exception as e:
            logger.error(f"Error checking URL {url}: {str(e)}")
            raise

    async def check_multiple_urls(self, urls: list[str], save_formats: list = ["markdown"]) -> list[dict]:
        """
        Check multiple URLs for compliance.

        Args:
            urls: List of dealership website URLs
            save_formats: List of report formats to save

        Returns:
            List of analysis results
        """
        logger.info(f"Starting compliance check for {len(urls)} URLs")

        results = []
        for i, url in enumerate(urls, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing URL {i}/{len(urls)}: {url}")
            logger.info(f"{'='*60}\n")

            try:
                result = await self.check_url(url, save_formats)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {url}: {str(e)}")
                results.append({
                    "url": url,
                    "error": str(e),
                    "compliance_status": "error"
                })

        logger.info(f"\n{'='*60}")
        logger.info(f"Completed checking {len(urls)} URLs")
        logger.info(f"Successful: {sum(1 for r in results if 'error' not in r)}")
        logger.info(f"Failed: {sum(1 for r in results if 'error' in r)}")
        logger.info(f"{'='*60}\n")

        return results

    def print_summary(self, result: dict):
        """
        Print a summary of the compliance check results.

        Args:
            result: Analysis result dictionary
        """
        if 'error' in result:
            print(f"\n❌ Error checking {result['url']}: {result['error']}\n")
            return

        status_emoji = {
            "compliant": "✅",
            "needs_review": "⚠️",
            "non_compliant": "❌"
        }.get(result.get('compliance_status', ''), "❓")

        print(f"\n{status_emoji} Compliance Check Results")
        print(f"{'='*60}")
        print(f"URL: {result.get('url', 'N/A')}")
        print(f"State: {result.get('state', 'N/A')}")
        print(f"Status: {result.get('compliance_status', 'Unknown').upper()}")
        print(f"Score: {result.get('overall_compliance_score', 0)}/100")
        print(f"\nSummary: {result.get('summary', 'No summary available')}")

        violations = result.get('violations', [])
        if violations:
            print(f"\n⚠️  {len(violations)} violation(s) found:")
            for i, v in enumerate(violations[:3], 1):  # Show first 3
                print(f"  {i}. [{v.get('severity', 'N/A').upper()}] {v.get('rule_violated', 'Unknown')}")
            if len(violations) > 3:
                print(f"  ... and {len(violations) - 3} more")

        print(f"\nReports saved:")
        for format, path in result.get('report_paths', {}).items():
            print(f"  {format}: {path}")
        print(f"{'='*60}\n")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Auto Dealership Compliance Checker - Analyze dealership websites for regulatory compliance"
    )
    parser.add_argument(
        "urls",
        nargs="+",
        help="One or more dealership website URLs to check"
    )
    parser.add_argument(
        "-s", "--state",
        required=True,
        choices=list(STATE_REGULATIONS.keys()),
        help="State code for compliance rules (e.g., CA, TX, NY, OK)"
    )
    parser.add_argument(
        "-f", "--formats",
        nargs="+",
        default=["markdown"],
        choices=["markdown", "json", "html"],
        help="Report formats to generate (default: markdown)"
    )
    parser.add_argument(
        "-o", "--output",
        default="reports",
        help="Output directory for reports (default: reports)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Initialize checker
        checker = ComplianceChecker(
            state_code=args.state,
            output_dir=args.output
        )

        # Check URLs
        if len(args.urls) == 1:
            result = await checker.check_url(args.urls[0], save_formats=args.formats)
            checker.print_summary(result)
        else:
            results = await checker.check_multiple_urls(args.urls, save_formats=args.formats)
            for result in results:
                checker.print_summary(result)

        logger.info("✓ All checks completed successfully")
        return 0

    except KeyboardInterrupt:
        logger.info("\n\nInterrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
