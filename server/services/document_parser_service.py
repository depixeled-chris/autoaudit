"""Document parsing service for legislation sources."""

import os
import logging
from typing import Dict, Optional, List
from datetime import date
from openai import AsyncOpenAI
from PyPDF2 import PdfReader
import io

logger = logging.getLogger(__name__)


class DocumentParserService:
    """Service for parsing uploaded documents into legislation sources."""

    def __init__(self):
        """Initialize the document parser service."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")

        self.client = AsyncOpenAI(api_key=api_key)
        logger.info("DocumentParserService initialized")

    async def parse_document(
        self,
        file_content: bytes,
        filename: str,
        state_code: str,
        mime_type: str
    ) -> Dict:
        """
        Parse an uploaded document and extract legislation information.

        Args:
            file_content: Raw file bytes
            filename: Original filename
            state_code: Two-letter state code
            mime_type: MIME type of the file

        Returns:
            Dictionary with parsed legislation data
        """
        logger.info(f"Parsing document: {filename} ({mime_type}) for state {state_code}")

        # Extract text based on file type
        text = await self._extract_text(file_content, mime_type, filename)

        if not text or len(text.strip()) < 100:
            raise ValueError("Document appears to be empty or too short to parse")

        # Use LLM to parse the legislation
        parsed_data = await self._parse_with_llm(text, state_code, filename)

        return parsed_data

    async def _extract_text(self, file_content: bytes, mime_type: str, filename: str) -> str:
        """Extract text from different file types."""

        # PDF extraction
        if mime_type == "application/pdf" or filename.lower().endswith(".pdf"):
            return self._extract_pdf_text(file_content)

        # Markdown or plain text
        elif mime_type in ["text/markdown", "text/plain"] or filename.lower().endswith((".md", ".txt")):
            try:
                return file_content.decode("utf-8")
            except UnicodeDecodeError:
                # Try with latin-1 as fallback
                return file_content.decode("latin-1")

        else:
            raise ValueError(f"Unsupported file type: {mime_type}. Supported types: PDF, Markdown (.md), Plain Text (.txt)")

    def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF file."""
        try:
            pdf_file = io.BytesIO(file_content)
            reader = PdfReader(pdf_file)

            text_parts = []
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"\n--- Page {page_num + 1} ---\n{page_text}")
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")

            full_text = "\n".join(text_parts)

            if not full_text.strip():
                raise ValueError("PDF appears to be empty or contains only images")

            return full_text

        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    async def _parse_with_llm(self, text: str, state_code: str, filename: str) -> Dict:
        """Use LLM to parse legislation text and extract structured information."""

        prompt = f"""You are a legal document parser specializing in automotive dealership advertising regulations.

Analyze the following legislation document and extract structured information.

**State Code:** {state_code}
**Document Filename:** {filename}

**Document Text:**
{text[:15000]}  # Limit to ~15k chars to stay within token limits

---

Extract the following information and respond with a JSON object:

{{
  "statute_number": "The statute, regulation, or code section number (e.g., '465:15-3-8', 'CAL. CIV. CODE § 2982')",
  "title": "Short descriptive title of the legislation (e.g., 'Vehicle Advertising Requirements')",
  "full_text": "Complete undoctored text of the statute or regulation",
  "source_url": "URL if mentioned in the document, otherwise null",
  "effective_date": "Effective date in YYYY-MM-DD format if mentioned, otherwise null",
  "sunset_date": "Sunset/expiration date in YYYY-MM-DD format if mentioned, otherwise null",
  "applies_to_page_types": "Comma-separated list of applicable page types. Choose from: VDP (vehicle detail page), INVENTORY (search/listing pages), HOMEPAGE, FINANCING, SERVICE, PARTS, ABOUT, CONTACT, SPECIALS. If applies to all advertising, use 'VDP,INVENTORY,HOMEPAGE,SPECIALS'. If not specified, leave null.",
  "digests": [
    {{
      "digest_type": "universal or page_specific",
      "page_type_code": "Page type code if digest_type is page_specific, otherwise null",
      "interpreted_requirements": "Plain language interpretation of what the statute requires or prohibits for compliance. Be specific and actionable. Format as a bulleted list."
    }}
  ]
}}

**Important Instructions:**
1. The "full_text" field should contain the COMPLETE, UNDOCTORED statutory text exactly as written
2. For "interpreted_requirements", translate legal language into clear, actionable compliance requirements
3. If the legislation applies to specific page types (e.g., only vehicle listings, only financing pages), create page_specific digests
4. If the legislation applies broadly to all advertising, create a universal digest
5. You can create multiple digests if different sections apply to different page types
6. Be precise with statute numbers - include all section identifiers, subsections, and references
7. If information is not present in the document, use null for that field

Respond ONLY with valid JSON, no additional text."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cost-effective for parsing
                messages=[
                    {
                        "role": "system",
                        "content": "You are a legal document parser. You extract structured information from legislation documents and return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=4000,
                response_format={"type": "json_object"}  # Ensure JSON response
            )

            # Parse the JSON response
            import json
            result_text = response.choices[0].message.content
            parsed_data = json.loads(result_text)

            # Validate required fields
            required_fields = ["statute_number", "title", "full_text"]
            for field in required_fields:
                if not parsed_data.get(field):
                    raise ValueError(f"LLM failed to extract required field: {field}")

            # Normalize digests - convert list to string if needed
            if parsed_data.get("digests"):
                for digest in parsed_data["digests"]:
                    if isinstance(digest.get("interpreted_requirements"), list):
                        # Convert list to bulleted string
                        digest["interpreted_requirements"] = "\n".join(
                            f"• {item}" if not item.strip().startswith(("•", "-", "*")) else item
                            for item in digest["interpreted_requirements"]
                        )

            logger.info(f"Successfully parsed legislation: {parsed_data['statute_number']}")
            return parsed_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            raise ValueError("Failed to parse document: LLM returned invalid JSON")

        except Exception as e:
            logger.error(f"LLM parsing error: {e}")
            raise ValueError(f"Failed to parse document with LLM: {str(e)}")

    async def parse_legislation_to_rules(
        self,
        legislation_text: str,
        state_code: str,
        statute_number: str
    ) -> List[Dict]:
        """
        Parse legislation text into individual atomic rules.

        Args:
            legislation_text: Full text of the legislation
            state_code: Two-letter state code
            statute_number: Statute or regulation number

        Returns:
            List of rule dictionaries with rule_text and applies_to_page_types
        """
        logger.info(f"Parsing legislation {statute_number} into rules for state {state_code}")

        prompt = f"""You are a legal document analyzer specializing in automotive dealership advertising regulations.

Analyze the following legislation and extract individual, atomic compliance rules.

**State Code:** {state_code}
**Statute Number:** {statute_number}

**Legislation Text:**
{legislation_text[:15000]}  # Limit to ~15k chars to stay within token limits

---

Extract individual compliance rules and respond with a JSON object:

{{
  "rules": [
    {{
      "rule_text": "Single, atomic compliance requirement in plain language. Be specific and actionable.",
      "applies_to_page_types": "Comma-separated list of applicable page types (VDP,INVENTORY,HOMEPAGE,FINANCING,SERVICE,PARTS,ABOUT,CONTACT,SPECIALS) or null if applies universally"
    }}
  ]
}}

**Important Instructions:**

1. **Atomic Rules**: Each rule should be a single, testable requirement
   - Good: "Vehicle price must include all mandatory fees"
   - Bad: "Pricing must be accurate and include fees and discounts properly displayed"

2. **Clear and Actionable**: Rules should be specific enough to check compliance
   - Good: "Advertised APR must not exceed the rate in financing documents"
   - Bad: "Interest rates should be reasonable"

3. **Page Type Specificity**: If a rule applies to specific page types, specify them
   - For vehicle listings/details: "VDP,INVENTORY"
   - For financing pages: "FINANCING"
   - For all advertising: null or "VDP,INVENTORY,HOMEPAGE,SPECIALS"

4. **Separate Requirements**: If legislation contains multiple requirements, create separate rules
   - Example: "Vehicles must show year, make, model" → 3 separate rules or 1 combined if they're always together

5. **Focus on Verifiable Requirements**: Extract rules that can be checked programmatically or visually
   - Include: disclosure requirements, mandatory information, prohibited practices, format requirements
   - Exclude: general principles without specific requirements

6. **Plain Language**: Translate legal jargon into clear business requirements
   - Legal: "Notwithstanding any provision to the contrary..."
   - Plain: "Dealerships must display..."

Respond ONLY with valid JSON, no additional text."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cost-effective
                messages=[
                    {
                        "role": "system",
                        "content": "You are a legal analyst that extracts atomic compliance rules from legislation. You return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=4000,
                response_format={"type": "json_object"}  # Ensure JSON response
            )

            # Parse the JSON response
            import json
            result_text = response.choices[0].message.content
            parsed_data = json.loads(result_text)

            # Validate and extract rules
            rules = parsed_data.get("rules", [])

            if not rules:
                raise ValueError("LLM failed to extract any rules from legislation")

            # Validate each rule
            for rule in rules:
                if not rule.get("rule_text"):
                    raise ValueError("Rule missing required 'rule_text' field")

            logger.info(f"Successfully extracted {len(rules)} rules from legislation {statute_number}")
            return rules

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            raise ValueError("Failed to parse legislation: LLM returned invalid JSON")

        except Exception as e:
            logger.error(f"LLM rule parsing error: {e}")
            raise ValueError(f"Failed to parse legislation into rules: {str(e)}")
