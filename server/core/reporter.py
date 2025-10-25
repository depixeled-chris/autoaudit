"""Generate compliance reports in various formats."""

import json
from datetime import datetime
from typing import Dict, List
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComplianceReporter:
    """Generates compliance reports from analysis results."""

    def __init__(self, output_dir: str = "reports"):
        """
        Initialize the reporter.

        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        logger.info(f"Reporter initialized. Output directory: {self.output_dir}")

    def generate_report(self, analysis_result: Dict, format: str = "markdown") -> str:
        """
        Generate a compliance report.

        Args:
            analysis_result: Analysis results from ComplianceAnalyzer
            format: Report format (markdown, json, or html)

        Returns:
            Report content as string
        """
        if format == "markdown":
            return self._generate_markdown_report(analysis_result)
        elif format == "json":
            return self._generate_json_report(analysis_result)
        elif format == "html":
            return self._generate_html_report(analysis_result)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_markdown_report(self, result: Dict) -> str:
        """Generate a Markdown compliance report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Determine status emoji
        status = result.get("compliance_status", "unknown")
        status_emoji = {
            "compliant": "✅",
            "needs_review": "⚠️",
            "non_compliant": "❌"
        }.get(status, "❓")

        report = f"""# Auto Dealership Compliance Report

**Generated:** {timestamp}
**URL:** {result.get('url', 'N/A')}
**State:** {result.get('state', 'N/A')}
**Model Used:** {result.get('model_used', 'N/A')}
**Tokens Used:** {result.get('tokens_used', 'N/A')}

---

## Overall Compliance Status

{status_emoji} **{status.upper()}**
**Score:** {result.get('overall_compliance_score', 0)}/100

### Summary
{result.get('summary', 'No summary available.')}

---

## Violations Found

"""
        violations = result.get('violations', [])
        if violations:
            for i, violation in enumerate(violations, 1):
                severity_emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(violation.get('severity', ''), "⚪")

                report += f"""### {i}. {violation.get('rule_violated', 'Unknown Rule')}

**Category:** {violation.get('category', 'N/A')}
**Severity:** {severity_emoji} {violation.get('severity', 'N/A').upper()}

**Description:**
{violation.get('description', 'No description provided.')}

**Evidence:**
> {violation.get('evidence', 'No evidence cited.')}

**Recommendation:**
{violation.get('recommendation', 'No recommendation provided.')}

---

"""
        else:
            report += "No violations found.\n\n---\n\n"

        # Compliant items
        report += "## Compliant Items\n\n"
        compliant = result.get('compliant_items', [])
        if compliant:
            for item in compliant:
                report += f"""- **{item.get('rule', 'Unknown')}** ({item.get('category', 'N/A')})
  Evidence: _{item.get('evidence', 'N/A')}_

"""
        else:
            report += "No compliant items specifically identified.\n\n"

        # Missing information
        report += "## Missing Information\n\n"
        missing = result.get('missing_information', [])
        if missing:
            for item in missing:
                report += f"- {item}\n"
        else:
            report += "No missing required information identified.\n"

        # Recommendations
        report += "\n## Recommendations\n\n"
        recommendations = result.get('recommendations', [])
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                report += f"{i}. {rec}\n"
        else:
            report += "No additional recommendations.\n"

        report += "\n---\n\n*This report was generated automatically using AI analysis. Please review all findings with legal counsel.*\n"

        return report

    def _generate_json_report(self, result: Dict) -> str:
        """Generate a JSON compliance report."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "report_version": "1.0",
            **result
        }
        return json.dumps(report, indent=2)

    def _generate_html_report(self, result: Dict) -> str:
        """Generate an HTML compliance report."""
        markdown_report = self._generate_markdown_report(result)

        # Simple markdown to HTML conversion (basic)
        html_content = markdown_report.replace('\n', '<br>\n')
        html_content = html_content.replace('# ', '<h1>').replace('\n<br>', '</h1>\n')
        html_content = html_content.replace('## ', '<h2>').replace('\n<br>', '</h2>\n')
        html_content = html_content.replace('### ', '<h3>').replace('\n<br>', '</h3>\n')
        html_content = html_content.replace('**', '<strong>').replace('**', '</strong>')
        html_content = html_content.replace('*', '<em>').replace('*', '</em>')

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Compliance Report - {result.get('url', 'Unknown')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
        h3 {{ color: #555; }}
        .status {{ font-size: 24px; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .compliant {{ background: #d4edda; border-left: 5px solid #28a745; }}
        .needs_review {{ background: #fff3cd; border-left: 5px solid #ffc107; }}
        .non_compliant {{ background: #f8d7da; border-left: 5px solid #dc3545; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
        blockquote {{
            background: #f9f9f9;
            border-left: 4px solid #ccc;
            padding: 10px 15px;
            margin: 10px 0;
            font-style: italic;
        }}
        .violation {{
            background: #fff;
            border: 1px solid #ddd;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_content}
    </div>
</body>
</html>
"""
        return html

    def save_report(self, analysis_result: Dict, filename: str = None, format: str = "markdown") -> str:
        """
        Generate and save a compliance report to disk.

        Args:
            analysis_result: Analysis results
            filename: Output filename (auto-generated if None)
            format: Report format

        Returns:
            Path to saved report
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            url_slug = analysis_result.get('url', 'unknown').replace('https://', '').replace('http://', '').replace('/', '_')[:50]
            ext = {"markdown": "md", "json": "json", "html": "html"}.get(format, "txt")
            filename = f"compliance_report_{url_slug}_{timestamp}.{ext}"

        report_content = self.generate_report(analysis_result, format)
        output_path = self.output_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"Report saved to: {output_path}")
        return str(output_path)

    def save_all_formats(self, analysis_result: Dict, base_filename: str = None) -> Dict[str, str]:
        """
        Save report in all available formats.

        Args:
            analysis_result: Analysis results
            base_filename: Base filename without extension

        Returns:
            Dictionary mapping format to file path
        """
        if base_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            url_slug = analysis_result.get('url', 'unknown').replace('https://', '').replace('http://', '').replace('/', '_')[:50]
            base_filename = f"compliance_report_{url_slug}_{timestamp}"

        paths = {}
        for format in ["markdown", "json", "html"]:
            ext = {"markdown": "md", "json": "json", "html": "html"}[format]
            filename = f"{base_filename}.{ext}"
            paths[format] = self.save_report(analysis_result, filename, format)

        return paths


def main():
    """Example usage."""
    sample_result = {
        "url": "https://example-dealership.com",
        "state": "California",
        "model_used": "gpt-4o-mini",
        "tokens_used": 1234,
        "overall_compliance_score": 65,
        "compliance_status": "needs_review",
        "summary": "The website has several compliance issues primarily related to incomplete pricing disclosures and missing financing terms.",
        "violations": [
            {
                "category": "pricing",
                "severity": "high",
                "rule_violated": "Advertised price must include all dealer-imposed fees",
                "description": "The advertised price does not clearly indicate whether dealer fees are included.",
                "evidence": "Price: $28,999* (*Plus taxes and fees)",
                "recommendation": "Clearly state all dealer-imposed fees in the advertised price or provide a complete breakdown."
            }
        ],
        "compliant_items": [
            {
                "category": "disclosure",
                "rule": "Vehicle history report availability",
                "evidence": "Free CARFAX report available"
            }
        ],
        "missing_information": [
            "Smog certification status",
            "APR disclosure for financing"
        ],
        "recommendations": [
            "Add clear APR disclosure to all financing mentions",
            "Include smog certification status for California sales"
        ]
    }

    reporter = ComplianceReporter()

    # Generate markdown report
    markdown_report = reporter.generate_report(sample_result, format="markdown")
    print(markdown_report)

    # Save all formats
    paths = reporter.save_all_formats(sample_result)
    print("\nReports saved:")
    for format, path in paths.items():
        print(f"  {format}: {path}")


if __name__ == "__main__":
    main()
