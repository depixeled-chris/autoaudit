"""Main orchestration script with hybrid text + visual verification."""

import asyncio
import argparse
import sys
import logging
from typing import Optional, List, Dict

from .scraper import DealershipScraper
from .converter import ContentConverter
from .analyzer import ComplianceAnalyzer
from .visual_analyzer import VisualComplianceAnalyzer
from .template_manager import TemplateManager
from .extraction_templates import ExtractionTemplateManager
from .reporter import ComplianceReporter
from .config import STATE_REGULATIONS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HybridComplianceChecker:
    """Multi-tier compliance checker with text + visual verification."""

    def __init__(self, state_code: str, output_dir: str = "reports"):
        """
        Initialize the hybrid compliance checker.

        Args:
            state_code: Two-letter state code
            output_dir: Directory to save reports
        """
        if state_code not in STATE_REGULATIONS:
            raise ValueError(f"State '{state_code}' not supported. Available: {list(STATE_REGULATIONS.keys())}")

        self.state_code = state_code
        self.state_rules = STATE_REGULATIONS[state_code]
        self.converter = ContentConverter()
        self.analyzer = ComplianceAnalyzer()
        self.visual_analyzer = VisualComplianceAnalyzer()
        self.template_manager = TemplateManager()
        self.extraction_manager = ExtractionTemplateManager()
        self.reporter = ComplianceReporter(output_dir)

        logger.info(f"HybridComplianceChecker initialized for {self.state_rules.state}")

    async def check_url(self, url: str, save_formats: list = ["markdown"], skip_visual: bool = False, url_type: str = "VDP") -> dict:
        """
        Check a single URL with hybrid text + visual verification.

        Args:
            url: Dealership website URL
            save_formats: List of report formats to save
            skip_visual: If True, skip visual verification (for testing)
            url_type: Type of URL (VDP, INVENTORY, HOMEPAGE, etc.)

        Returns:
            Analysis results dictionary
        """
        logger.info(f"Starting hybrid compliance check for: {url} (Type: {url_type})")

        try:
            # Step 1 & 2: Scrape and extract with templates
            logger.info("Step 1/5: Scraping website...")

            scraper = DealershipScraper()
            await scraper.start()

            try:
                # Initial scrape for metadata
                scraped_data = await scraper.scrape_page(url)
                logger.info(f"✓ Scraped successfully. Platform: {scraped_data['platform']}")

                # Detect template
                template_id = self.template_manager.detect_template(
                    url=url,
                    platform=scraped_data['platform'],
                    html=scraped_data['html']
                )
                logger.info(f"Detected template: {template_id}")

                # Step 2: Extract content using templates
                logger.info("Step 2/5: Extracting content with templates...")

                # Open page for template-based extraction
                page = await scraper.browser.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)

                # Get extraction template based on URL type
                extraction_template = self.extraction_manager.get_template(
                    url=url,
                    platform=scraped_data['platform'],
                    url_type=url_type
                )

                # Extract structured content
                extracted_sections = await extraction_template.extract(page)

                # Also get cleaned HTML for fallback
                clean_html = await extraction_template.get_clean_html(page)

                # Convert to markdown
                if extracted_sections:
                    # Build markdown from extracted sections
                    llm_input = "# Vehicle Detail Page Content\n\n"
                    for section_name, content in extracted_sections.items():
                        llm_input += f"## {section_name.replace('_', ' ').title()}\n{content}\n\n"
                    logger.info(f"✓ Extracted {len(extracted_sections)} sections using template")
                else:
                    # Fallback to full HTML conversion
                    markdown = self.converter.html_to_markdown(clean_html)
                    sections = self.converter.extract_sections(markdown, scraped_data)
                    llm_input = self.converter.prepare_for_llm(sections)
                    logger.info("✓ Using fallback HTML-to-markdown conversion")

                await page.close()
            finally:
                await scraper.close()

            logger.info(f"✓ Converted to Markdown ({len(llm_input)} characters)")

            # Save LLM input
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
                f.write(f"**Template:** {template_id}\n")
                f.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Character Count:** {len(llm_input)}\n\n")
                f.write("---\n\n")
                f.write(llm_input)

            logger.info(f"✓ LLM input saved to: {input_filename}")

            # Step 3: Text Analysis
            logger.info("Step 3/5: Analyzing compliance with LLM (text)...")
            text_result = await self.analyzer.analyze_compliance(
                content=llm_input,
                state_rules=self.state_rules,
                url=url,
                url_type=url_type
            )

            logger.info(f"✓ Text analysis complete. Score: {text_result.get('overall_compliance_score', 0)}/100")

            # Step 4: Visual Verification (if needed)
            # ALWAYS do visual verification for homepage scans
            force_visual_for_homepage = url_type.upper() == 'HOMEPAGE'
            visual_results = []
            if not skip_visual or force_visual_for_homepage:
                logger.info("Step 4/5: Checking for visual verification needs...")

                # Find violations that need visual verification
                # Lower threshold to 0.85 to trigger visual verification for spatial rules
                needs_visual = [
                    v for v in text_result.get('violations', [])
                    if v.get('needs_visual_verification', False) and v.get('confidence', 1.0) < 0.85
                ]

                # For homepages, ALWAYS do visual verification of key contact info
                # even if no violations are flagged
                if force_visual_for_homepage and not needs_visual:
                    logger.info("Homepage detected - forcing visual verification of contact information")
                    # Create synthetic verification task for contact info visibility
                    needs_visual.append({
                        'rule_key': 'homepage_contact_visibility',
                        'rule_violated': 'Physical address, phone number, and business hours must be conspicuous and easily accessible',
                        'needs_visual_verification': True
                    })

                if needs_visual:
                    logger.info(f"Found {len(needs_visual)} violation(s) needing visual verification")

                    # Scrape again with browser for screenshot
                    async with DealershipScraper() as scraper:
                        browser = scraper.browser
                        page = await browser.new_page()
                        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

                        for violation in needs_visual:
                            rule_key = violation.get('rule_key', '')
                            rule_text = violation.get('rule_violated', '')

                            # Check template cache first
                            if self.template_manager.should_skip_visual_verification(template_id, rule_key):
                                cached = self.template_manager.get_rule_status(template_id, rule_key)
                                logger.info(f"✓ Using cached decision for {rule_key}: {cached['status']}")

                                visual_results.append({
                                    'rule_key': rule_key,
                                    'rule': rule_text,
                                    'cached': True,
                                    'is_compliant': cached['status'] == 'compliant',
                                    'confidence': cached['confidence'],
                                    'verification_method': 'cached',
                                    'notes': cached.get('notes', '')
                                })
                            else:
                                # Perform visual verification
                                logger.info(f"Performing visual verification for: {rule_key}")

                                visual_result = await self.visual_analyzer.capture_and_verify(
                                    page=page,
                                    rule=rule_text,
                                    context={
                                        'url': url,
                                        'state': self.state_rules.state,
                                        'template_id': template_id
                                    }
                                )

                                visual_results.append(visual_result)

                                # Update template cache
                                self.template_manager.update_rule_status(
                                    template_id=template_id,
                                    rule=rule_key,
                                    status='compliant' if visual_result['is_compliant'] else 'non_compliant',
                                    confidence=visual_result['confidence'],
                                    verification_method='visual',
                                    notes=visual_result.get('visual_evidence', '')
                                )

                                logger.info(f"✓ Visual verification complete: {visual_result['is_compliant']}")

                        await page.close()

                    logger.info(f"✓ Visual verification complete for {len(visual_results)} rule(s)")
                else:
                    logger.info("✓ No visual verification needed (high text confidence)")
            else:
                logger.info("Step 4/5: Skipping visual verification (skip_visual=True)")

            # Merge visual results into text results
            text_result['visual_verifications'] = visual_results
            text_result['template_id'] = template_id

            # Calculate token usage
            text_tokens = text_result.get('tokens_used', 0)
            visual_tokens = sum(v.get('tokens_used', 0) for v in visual_results)
            total_tokens = text_tokens + visual_tokens

            text_result['text_analysis_tokens'] = text_tokens
            text_result['visual_tokens'] = visual_tokens
            text_result['total_tokens'] = total_tokens

            logger.info(f"✓ Token usage - Text: {text_tokens}, Visual: {visual_tokens}, Total: {total_tokens}")

            # Step 5: Generate reports
            logger.info("Step 5/5: Generating reports...")
            saved_reports = {}
            for format in save_formats:
                report_path = self.reporter.save_report(text_result, format=format)
                saved_reports[format] = report_path

            logger.info(f"✓ Reports saved: {', '.join(saved_reports.values())}")

            # Add report paths to result
            text_result['report_paths'] = saved_reports

            return text_result

        except Exception as e:
            logger.error(f"Error checking URL {url}: {str(e)}")
            raise

    def print_summary(self, result: dict):
        """Print a summary of the compliance check results."""
        if 'error' in result:
            print(f"\n❌ Error checking {result['url']}: {result['error']}\n")
            return

        print(f"\n{'='*80}")
        print(f"HYBRID COMPLIANCE CHECK RESULTS")
        print(f"{'='*80}")
        print(f"URL: {result.get('url', 'N/A')}")
        print(f"State: {result.get('state', 'N/A')}")
        print(f"Template: {result.get('template_id', 'N/A')}")
        print(f"Status: {result.get('compliance_status', 'Unknown').upper()}")
        print(f"Score: {result.get('overall_compliance_score', 0)}/100")
        print(f"\nSummary: {result.get('summary', 'No summary available')}")

        # Text violations
        violations = result.get('violations', [])
        if violations:
            print(f"\n{'-'*80}")
            print(f"TEXT ANALYSIS VIOLATIONS ({len(violations)} found):")
            print(f"{'-'*80}")
            for i, v in enumerate(violations, 1):
                print(f"\n{i}. [{v.get('severity', 'N/A').upper()}] {v.get('rule_violated', 'Unknown')}")
                print(f"   Confidence: {v.get('confidence', 'N/A')}")
                print(f"   Needs Visual: {v.get('needs_visual_verification', False)}")

        # Visual verifications
        visual = result.get('visual_verifications', [])
        if visual:
            print(f"\n{'-'*80}")
            print(f"VISUAL VERIFICATIONS ({len(visual)} performed):")
            print(f"{'-'*80}")
            for i, v in enumerate(visual, 1):
                status = "✓ COMPLIANT" if v.get('is_compliant') else "✗ NON-COMPLIANT"
                cached = " (CACHED)" if v.get('cached') else " (NEW)"
                print(f"\n{i}. {v.get('rule', 'Unknown')}")
                print(f"   Result: {status}{cached}")
                print(f"   Confidence: {v.get('confidence', 'N/A')}")
                if not v.get('cached'):
                    print(f"   Evidence: {v.get('visual_evidence', 'N/A')[:100]}...")

        print(f"\n{'-'*80}")
        print(f"REPORTS GENERATED:")
        print(f"{'-'*80}")
        for format, path in result.get('report_paths', {}).items():
            print(f"  {format}: {path}")
        print(f"{'='*80}\n")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Hybrid Auto Dealership Compliance Checker - Text + Visual Analysis"
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
        "--skip-visual",
        action="store_true",
        help="Skip visual verification (text analysis only)"
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
        checker = HybridComplianceChecker(
            state_code=args.state,
            output_dir=args.output
        )

        # Check URLs
        for url in args.urls:
            result = await checker.check_url(url, save_formats=args.formats, skip_visual=args.skip_visual)
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
