"""HTML to Markdown conversion with content cleaning."""

import html2text
import re
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentConverter:
    """Converts HTML content to clean Markdown suitable for LLM processing."""

    def __init__(self):
        self.h2t = html2text.HTML2Text()
        # Configure html2text
        self.h2t.ignore_links = False
        self.h2t.ignore_images = True
        self.h2t.ignore_emphasis = False
        self.h2t.body_width = 0  # Don't wrap lines
        self.h2t.single_line_break = False

    def html_to_markdown(self, html: str) -> str:
        """
        Convert HTML to Markdown.

        Args:
            html: Raw HTML content

        Returns:
            Cleaned Markdown string
        """
        try:
            # Convert to markdown
            markdown = self.h2t.handle(html)

            # Clean up the markdown
            markdown = self._clean_markdown(markdown)

            return markdown
        except Exception as e:
            logger.error(f"Error converting HTML to Markdown: {str(e)}")
            raise

    def _clean_markdown(self, markdown: str) -> str:
        """
        Clean up converted markdown content.

        Args:
            markdown: Raw markdown from html2text

        Returns:
            Cleaned markdown
        """
        # Remove excessive newlines (more than 2 consecutive)
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)

        # Remove common navigation/footer noise patterns
        noise_patterns = [
            r'(Skip to|Jump to) (main content|navigation)',
            r'Copyright \d{4}.*',
            r'All rights reserved',
            r'Privacy Policy.*Terms.*',
            r'\[Image\]',  # Image placeholders
            r'\* \* \*',  # Decorative separators
        ]

        for pattern in noise_patterns:
            markdown = re.sub(pattern, '', markdown, flags=re.IGNORECASE)

        # Remove script/style remnants
        markdown = re.sub(r'var \w+\s*=.*?;', '', markdown)
        markdown = re.sub(r'function.*?\{.*?\}', '', markdown, flags=re.DOTALL)

        # Clean up extra whitespace
        markdown = re.sub(r' +', ' ', markdown)
        markdown = re.sub(r'\n ', '\n', markdown)

        return markdown.strip()

    def extract_sections(self, markdown: str, scraped_data: Dict) -> Dict[str, str]:
        """
        Extract key sections from markdown for targeted analysis.

        Args:
            markdown: Full markdown content
            scraped_data: Original scraped data with metadata

        Returns:
            Dictionary of extracted sections
        """
        sections = {
            "full_content": markdown,
            "title": scraped_data.get("title", ""),
            "url": scraped_data.get("url", ""),
            "platform": scraped_data.get("platform", "unknown"),
        }

        # Try to extract specific sections
        sections["pricing"] = self._extract_section(markdown, ["price", "pricing", "payment", "finance", "lease", "msrp"])
        sections["inventory"] = self._extract_section(markdown, ["inventory", "vehicle", "stock", "vin"])
        sections["disclaimers"] = self._extract_section(markdown, ["disclaimer", "disclosure", "terms", "conditions"])
        sections["contact"] = self._extract_section(markdown, ["contact", "location", "hours", "phone"])

        return sections

    def _extract_section(self, markdown: str, keywords: list[str]) -> str:
        """
        Extract content sections based on keywords.

        Args:
            markdown: Markdown content
            keywords: List of keywords to search for

        Returns:
            Extracted section or empty string
        """
        lines = markdown.split('\n')
        section_lines = []
        in_section = False
        capture_count = 0

        for i, line in enumerate(lines):
            # Check if line contains any keyword
            if any(keyword in line.lower() for keyword in keywords):
                in_section = True
                capture_count = 0

            if in_section:
                section_lines.append(line)
                capture_count += 1

                # Stop after capturing ~20 lines or hitting a major header
                if capture_count > 20 or (capture_count > 5 and line.startswith('# ')):
                    in_section = False

        return '\n'.join(section_lines).strip()

    def prepare_for_llm(self, sections: Dict[str, str], max_length: int = 15000) -> str:
        """
        Prepare content for LLM analysis with token limits in mind.

        Args:
            sections: Dictionary of content sections
            max_length: Maximum character length (rough token approximation)

        Returns:
            Formatted string ready for LLM
        """
        # Prioritize important sections
        important_sections = ["pricing", "disclaimers", "inventory"]

        output = f"""# Website Analysis
URL: {sections['url']}
Title: {sections['title']}
Platform: {sections['platform']}

"""

        # Add important sections first
        for section_name in important_sections:
            if sections.get(section_name):
                output += f"## {section_name.title()}\n{sections[section_name]}\n\n"

        # Add full content if space allows (truncate if needed)
        remaining_space = max_length - len(output)
        if remaining_space > 1000:
            full_content = sections.get("full_content", "")
            if len(full_content) > remaining_space:
                full_content = full_content[:remaining_space] + "\n\n[Content truncated...]"
            output += f"## Full Page Content\n{full_content}\n"

        return output[:max_length]


def main():
    """Example usage."""
    sample_html = """
    <html>
        <head><title>ABC Motors - New & Used Cars</title></head>
        <body>
            <h1>Welcome to ABC Motors</h1>
            <div class="pricing">
                <h2>2024 Toyota Camry</h2>
                <p>Price: $28,999*</p>
                <p>*Plus taxes and fees</p>
            </div>
            <div class="disclaimer">
                <p>All prices subject to change. See dealer for details.</p>
            </div>
        </body>
    </html>
    """

    converter = ContentConverter()
    markdown = converter.html_to_markdown(sample_html)
    print("Converted Markdown:")
    print(markdown)

    scraped_data = {"title": "ABC Motors", "url": "https://example.com", "platform": "custom"}
    sections = converter.extract_sections(markdown, scraped_data)

    print("\n\nExtracted Sections:")
    for section_name, content in sections.items():
        if content:
            print(f"\n=== {section_name.upper()} ===")
            print(content[:200] + "..." if len(content) > 200 else content)


if __name__ == "__main__":
    main()
