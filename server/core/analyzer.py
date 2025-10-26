"""LLM-based compliance analysis using OpenAI API."""

import os
from typing import Dict, List, Optional
from openai import AsyncOpenAI
import json
import logging
from dotenv import load_dotenv

from .config import StateRules, OPENAI_MODEL, MAX_TOKENS, TEMPERATURE
from .url_type_preambles import get_preamble, get_url_type_name

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComplianceAnalyzer:
    """Analyzes dealership content for compliance using LLM."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the analyzer.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")

        self.client = AsyncOpenAI(api_key=self.api_key)
        logger.info("ComplianceAnalyzer initialized")

    async def analyze_compliance(
        self,
        content: str,
        state_rules: StateRules,
        url: str = "",
        url_type: str = "VDP"
    ) -> Dict:
        """
        Analyze content for compliance violations.

        Args:
            content: Markdown content from the dealership website
            state_rules: State-specific compliance rules
            url: Original URL (for reference)
            url_type: Type of URL (VDP, INVENTORY, HOMEPAGE, etc.)

        Returns:
            Dictionary containing compliance analysis results
        """
        logger.info(f"Analyzing compliance for {state_rules.state} ({url_type} page)")

        # Build the analysis prompt
        prompt = self._build_analysis_prompt(content, state_rules, url, url_type)

        # Save the full prompt with rules for review
        from datetime import datetime
        from pathlib import Path

        input_dir = Path("llm_inputs")
        input_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        url_slug = url.replace('https://', '').replace('http://', '').replace('/', '_')[:50]
        prompt_filename = input_dir / f"full_prompt_{url_slug}_{timestamp}.txt"

        with open(prompt_filename, 'w', encoding='utf-8') as f:
            f.write(f"# Complete Prompt Sent to GPT-4.1-nano\n\n")
            f.write(f"**URL:** {url}\n")
            f.write(f"**State:** {state_rules.state}\n")
            f.write(f"**URL Type:** {get_url_type_name(url_type)}\n")
            f.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Model:** {OPENAI_MODEL}\n")
            f.write(f"**Character Count:** {len(prompt)}\n\n")
            f.write("="*80 + "\n")
            f.write("SYSTEM MESSAGE:\n")
            f.write("="*80 + "\n\n")
            f.write("You are an expert in automotive dealership compliance and advertising regulations. Analyze the provided content for compliance violations with precision and cite specific examples.\n\n")
            f.write("="*80 + "\n")
            f.write("USER PROMPT:\n")
            f.write("="*80 + "\n\n")
            f.write(prompt)

        logger.info(f"Full prompt saved to: {prompt_filename}")

        try:
            # Call OpenAI API with structured output
            response = await self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in automotive dealership compliance and advertising regulations. Analyze the provided content for compliance violations with precision and cite specific examples."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_completion_tokens=MAX_TOKENS,
                response_format={"type": "json_object"}
            )

            # Parse the response
            result_text = response.choices[0].message.content
            logger.info(f"Response content: {result_text[:500] if result_text else 'None'}")

            if not result_text:
                raise ValueError("Empty response from API")

            result = json.loads(result_text)

            # Add metadata
            result["url"] = url
            result["state"] = state_rules.state
            result["model_used"] = OPENAI_MODEL
            result["tokens_used"] = response.usage.total_tokens

            logger.info(f"Analysis complete. Tokens used: {response.usage.total_tokens}")

            return result

        except Exception as e:
            logger.error(f"Error during LLM analysis: {str(e)}")
            raise

    def _build_analysis_prompt(self, content: str, state_rules: StateRules, url: str, url_type: str = "VDP") -> str:
        """
        Build the analysis prompt for the LLM.

        Args:
            content: Markdown content
            state_rules: State compliance rules
            url: Website URL
            url_type: Type of URL (VDP, INVENTORY, HOMEPAGE, etc.)

        Returns:
            Formatted prompt string
        """
        # Get URL type-specific preamble
        url_type_context = get_preamble(url_type)

        prompt = f"""Analyze the following auto dealership website content for compliance with {state_rules.state} regulations.

URL: {url}
Page Type: {get_url_type_name(url_type)}

{url_type_context}

# General Analysis Guidelines

When evaluating compliance, apply these principles:

**Interpretation of Terms:**
- "Adjacent to price" means within the same visual section or pricing module. If vehicle identification appears as a HEADING above the price section (even with a few lines between), it counts as adjacent. The key test: would a consumer looking at the price also see the vehicle identification without scrolling or changing focus? If yes, it's adjacent.
- "Conspicuous" means reasonably visible and readable to a typical consumer. Information doesn't need to be in the largest font or highlighted - it just needs to be in a logical location where consumers would naturally find it when reviewing the vehicle and pricing information.
- **Important**: If vehicle year/make/model appears in the page title, section heading, or within 10 lines of the price, consider it adjacent unless it's obviously hidden or in an unrelated section.
- Focus on the **spirit and intent** of regulations, not overly technical or pedantic interpretations. Regulations aim to prevent consumer deception, not punish reasonable layout choices.

**Evaluation Approach:**
- Give credit when information is present and reasonably accessible, even if placement isn't perfect.
- Distinguish between **substantive violations** (missing required information) and **technical violations** (information present but formatting could be improved).
- Flag as violations only when information is truly missing, misleading, or so poorly positioned that consumers would likely miss it.
- If a dealership has made a good-faith effort to comply and information is available, note areas for improvement rather than strict violations.

**Severity Assessment:**
- **Critical**: Required information completely missing or actively misleading
- **High**: Information present but poorly positioned/formatted, likely to cause consumer confusion
- **Medium**: Information present but could be more prominent or clear
- **Low**: Minor formatting improvements that would enhance compliance

**Balanced Reporting:**
- Actively look for and acknowledge compliant items - don't only focus on violations.
- Consider the overall user experience and whether consumers can reasonably find important information.
- Avoid flagging violations where the dealership has substantially met the requirement.

# State-Specific Requirements for {state_rules.state}

## Required Disclosures
{self._format_rules_list(state_rules.required_disclosures)}

## Pricing Rules
{self._format_rules_list(state_rules.pricing_rules)}

## Financing Rules
{self._format_rules_list(state_rules.financing_rules)}

# Website Content to Analyze

{content}

# Analysis Instructions

Please provide a compliance analysis in JSON format with the following structure:

{{
    "overall_compliance_score": <number 0-100>,
    "compliance_status": "<compliant|needs_review|non_compliant>",
    "violations": [
        {{
            "category": "<disclosure|pricing|financing>",
            "severity": "<critical|high|medium|low>",
            "rule_violated": "<specific rule from requirements>",
            "rule_key": "<short_snake_case_key_for_this_rule>",
            "confidence": <number 0.0-1.0 indicating confidence in this violation>,
            "description": "<what the violation is>",
            "evidence": "<quote from content showing the violation>",
            "recommendation": "<how to fix it>",
            "needs_visual_verification": <true/false - true if spatial/visual judgment is uncertain>
        }}
    ],
    "compliant_items": [
        {{
            "category": "<disclosure|pricing|financing>",
            "rule": "<specific rule>",
            "evidence": "<quote showing compliance>"
        }}
    ],
    "missing_information": [
        "<list of required items not found on the page>"
    ],
    "recommendations": [
        "<general recommendations for improving compliance>"
    ],
    "summary": "<brief 2-3 sentence summary of compliance status>"
}}

**Confidence and Visual Verification Guidelines:**
- Set "confidence" based on how certain you are from text alone:
  - 0.9-1.0: Extremely confident (information clearly present or clearly missing)
  - 0.7-0.9: Confident (likely correct but some ambiguity)
  - 0.5-0.7: Moderate confidence (text suggests violation but spatial/visual layout unclear)
  - 0.0-0.5: Low confidence (requires visual confirmation)

- Set "needs_visual_verification" to true when:
  - Judging spatial proximity ("adjacent to", "conspicuous")
  - Assessing visual hierarchy (font size, prominence)
  - Layout/positioning is critical to compliance
  - Confidence < 0.7 on HIGH or CRITICAL severity violations

- Set "rule_key" as a short identifier (e.g., "vehicle_id_adjacent", "dealer_name_conspicuous")

Be thorough and cite specific examples from the content. If information is not found, note it in missing_information.
"""
        return prompt

    def _format_rules_list(self, rules: List[str]) -> str:
        """Format a list of rules as markdown."""
        return "\n".join([f"- {rule}" for rule in rules])

    async def batch_analyze(
        self,
        contents: List[Dict[str, str]],
        state_rules: StateRules
    ) -> List[Dict]:
        """
        Analyze multiple pieces of content in batch.

        Args:
            contents: List of content dictionaries with 'content' and 'url' keys
            state_rules: State compliance rules

        Returns:
            List of analysis results
        """
        import asyncio

        tasks = [
            self.analyze_compliance(
                content=item["content"],
                state_rules=state_rules,
                url=item.get("url", "")
            )
            for item in contents
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to analyze {contents[i].get('url', 'unknown')}: {result}")
                valid_results.append({
                    "error": str(result),
                    "url": contents[i].get("url", "")
                })
            else:
                valid_results.append(result)

        return valid_results


async def main():
    """Example usage."""
    from config import STATE_REGULATIONS

    sample_content = """
    # ABC Motors - New Cars

    ## 2024 Toyota Camry
    Price: $28,999*

    *Plus taxes and fees

    ## Financing Available
    Low rates available! Contact us for details.

    ## Disclaimer
    All prices subject to change without notice.
    """

    analyzer = ComplianceAnalyzer()
    result = await analyzer.analyze_compliance(
        content=sample_content,
        state_rules=STATE_REGULATIONS["CA"],
        url="https://example-dealership.com"
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
