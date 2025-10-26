"""Page-type-specific compliance rules and contexts."""

from typing import Dict, List
from pydantic import BaseModel


class PageTypeRules(BaseModel):
    """Rules specific to a page type."""
    page_type: str
    description: str
    context_preamble: str
    applicable_rules: List[str]
    not_applicable_rules: List[str]
    specific_guidance: List[str]


# Oklahoma page-specific rules
OK_PAGE_TYPE_RULES: Dict[str, PageTypeRules] = {
    "HOMEPAGE": PageTypeRules(
        page_type="HOMEPAGE",
        description="Dealership homepage/landing page",
        context_preamble="""
This is a HOMEPAGE (dealership landing page), NOT a specific vehicle advertisement.

CRITICAL CONTEXT:
- Homepages showcase general inventory, promotions, and dealership information
- They typically do NOT advertise specific individual vehicles with prices
- Vehicle-specific disclosure rules (year/make/model adjacent to price) ONLY apply when specific vehicles are advertised with individual prices
- General promotional banners (e.g., "$X OFF MSRP") are NOT specific vehicle advertisements
- Dealership identity requirements (name, contact info) DO apply

DO NOT flag violations for vehicle-specific rules unless the homepage is actually advertising specific vehicles with individual prices.
""",
        applicable_rules=[
            "Dealership name must be conspicuously displayed in all advertisements (465:15-3-15)",
            "No misleading layouts, headlines, or type sizes (465:15-3-5)",
            "No bait-and-switch advertising (465:15-3-4)",
            "No false claims about financing guarantees like 'everybody financed' (465:15-3-14(1))",
            "Lease advertisements must clearly disclose the word 'lease' (465:15-3-12)",
            "'Liquidation', 'going out of business' only if actually closing (465:15-3-14(11))",
        ],
        not_applicable_rules=[
            "Vehicle identification (year, make, model) adjacent to price (465:15-3-8) - ONLY applies to specific vehicle ads",
            "Stock number required (465:15-3-2) - ONLY applies to specific vehicle ads",
            "Prior service disclosure (465:15-3-8(a)(4)) - ONLY applies to specific vehicle ads",
            "Number of vehicles available at advertised price (465:15-3-2) - ONLY applies to specific vehicle ads",
        ],
        specific_guidance=[
            "Look for dealership name in header, logo, or prominent location",
            "Check for contact information: phone, address, business hours",
            "General promotional offers (e.g., '$X OFF MSRP') do NOT require specific vehicle identification unless a specific vehicle is shown",
            "Inventory category links or 'Search by Model' sections are NOT individual vehicle advertisements",
            "A compliant homepage should clearly identify the dealership and provide contact info - that's the primary requirement",
        ]
    ),

    "VDP": PageTypeRules(
        page_type="VDP",
        description="Vehicle Detail Page - specific vehicle advertisement",
        context_preamble="""
This is a VEHICLE DETAIL PAGE (VDP) - a page advertising a SPECIFIC individual vehicle.

CRITICAL CONTEXT:
- This page advertises one specific vehicle with a specific price
- ALL vehicle-specific disclosure rules MUST be followed
- Vehicle identification (year, make, model) MUST be conspicuous and adjacent to price
- Stock numbers, prior service history, and all required disclosures MUST be present
- The price shown must be the full selling price (excluding only tax, title, license)

This is the most heavily regulated type of page - be thorough in checking compliance.
""",
        applicable_rules=[
            "Vehicle identification (year, make, model) must be conspicuously disclosed adjacent to price (465:15-3-8)",
            "Stock number required for single vehicle ads (465:15-3-2)",
            "Prior service disclosure required (demonstrator, service loaner, factory program vehicle, etc.) (465:15-3-8(a)(4))",
            "Dealership name must be conspicuously displayed (465:15-3-15)",
            "Most conspicuous price must be full selling price (only excluding tax, title, license) (465:15-3-7(a))",
            "No price qualifications like 'with trade', 'with acceptable trade', 'with dealer-arranged financing' (465:15-3-7(b))",
            "Rebates or incentives included in price must be clearly disclosed (465:15-3-7(c))",
            "Select consumer rebates must be shown separately or clearly identified (465:15-3-7(d))",
            "Savings claims only allowed from MSRP sticker price, not including Monroney discounts (465:15-3-14(5))",
            "No 'free' or 'complimentary' offers requiring purchase (465:15-3-14(6))",
            "MSRP cannot be inflated or misrepresented (465:15-3-6)",
            "No misleading layouts, headlines, or type sizes (465:15-3-5)",
            "Illustration must be of actual vehicle or same make/model/year/style (465:15-3-8(b))",
        ],
        not_applicable_rules=[
            "Number of vehicles available for advertised price (465:15-3-2) - only applies to multi-vehicle ads",
        ],
        specific_guidance=[
            "Vehicle year, make, and model MUST be adjacent to (near) the price - same visual section/card",
            "Check that price is the most prominent/conspicuous element",
            "Look for any price qualifications or conditions (these are violations)",
            "Verify rebates/incentives are clearly disclosed if included in price",
            "Check for stock number or VIN visibility",
            "Verify dealer name is clearly visible on the page",
        ]
    ),

    "INVENTORY": PageTypeRules(
        page_type="INVENTORY",
        description="Inventory listing page - multiple vehicles",
        context_preamble="""
This is an INVENTORY LISTING PAGE showing multiple vehicles.

CRITICAL CONTEXT:
- This page shows multiple vehicles, each with its own listing/card
- Each vehicle listing must follow individual vehicle advertisement rules
- If prices are shown, year/make/model must be adjacent to each price
- If a vehicle is shown with a price, treat it like a mini vehicle advertisement
- However, inventory filters, search options, and category headers are NOT advertisements

Apply vehicle-specific rules to each INDIVIDUAL VEHICLE LISTING that shows a price.
""",
        applicable_rules=[
            "Vehicle identification (year, make, model) must be adjacent to price for each listed vehicle (465:15-3-8)",
            "Dealership name must be conspicuously displayed (465:15-3-15)",
            "Most conspicuous price must be full selling price for each vehicle (465:15-3-7(a))",
            "No price qualifications like 'with trade' (465:15-3-7(b))",
            "Rebates included in price must be disclosed (465:15-3-7(c))",
            "No misleading layouts or type sizes (465:15-3-5)",
            "If multiple identical vehicles, quantity must be disclosed (465:15-3-2)",
        ],
        not_applicable_rules=[
            "Stock number required - not strictly required for inventory grid listings",
            "Prior service disclosure - typically disclosed on VDP, not required in listing cards",
        ],
        specific_guidance=[
            "Check each vehicle card/listing individually",
            "Year, make, model should be visible near the price on each card",
            "Inventory counts or 'X vehicles available' are acceptable disclosures",
            "Filter options and search tools are not advertisements - do not apply rules to them",
            "Focus on the actual vehicle listings with prices",
        ]
    ),

    "SRP": PageTypeRules(
        page_type="SRP",
        description="Search Results Page - filtered inventory",
        context_preamble="""
This is a SEARCH RESULTS PAGE (SRP) showing filtered inventory results.

CRITICAL CONTEXT:
- Similar to inventory page, but showing filtered/searched results
- Each vehicle result must follow individual vehicle advertisement rules
- Search filters, sort options, and result counts are NOT advertisements
- Apply rules to individual vehicle listings, not to the search interface

This is essentially an inventory page with search filters applied.
""",
        applicable_rules=[
            "Vehicle identification (year, make, model) must be adjacent to price for each result (465:15-3-8)",
            "Dealership name must be conspicuously displayed (465:15-3-15)",
            "Most conspicuous price must be full selling price (465:15-3-7(a))",
            "No price qualifications like 'with trade' (465:15-3-7(b))",
            "No misleading layouts or type sizes (465:15-3-5)",
        ],
        not_applicable_rules=[
            "Stock number required - not strictly required for search result cards",
            "Prior service disclosure - typically disclosed on VDP",
        ],
        specific_guidance=[
            "Apply rules to vehicle result cards, not search interface",
            "Each vehicle listing should show year/make/model near price",
            "Result counts, filters, and sort options are not advertisements",
        ]
    ),
}


def get_page_type_rules(state_code: str, page_type: str) -> PageTypeRules:
    """
    Get page-type-specific rules for a state.

    Args:
        state_code: Two-letter state code
        page_type: Page type (HOMEPAGE, VDP, INVENTORY, SRP)

    Returns:
        PageTypeRules object with context and applicable rules
    """
    # Currently only Oklahoma implemented
    if state_code == "OK":
        return OK_PAGE_TYPE_RULES.get(page_type.upper(), OK_PAGE_TYPE_RULES["VDP"])

    # Default to VDP rules if state not implemented
    return OK_PAGE_TYPE_RULES["VDP"]


def format_rules_for_prompt(state_code: str, page_type: str, base_rules: List[str]) -> str:
    """
    Format rules with page-type-specific context for LLM prompt.

    Args:
        state_code: Two-letter state code
        page_type: Page type
        base_rules: Base list of all rules for the state

    Returns:
        Formatted string with context and applicable rules
    """
    page_rules = get_page_type_rules(state_code, page_type)

    output = f"""
# PAGE TYPE: {page_rules.page_type}

{page_rules.context_preamble}

## APPLICABLE RULES FOR THIS PAGE TYPE:

"""

    # Add applicable rules
    for rule in page_rules.applicable_rules:
        output += f"✓ {rule}\n"

    output += "\n## RULES THAT DO NOT APPLY TO THIS PAGE TYPE:\n\n"

    # Add non-applicable rules
    for rule in page_rules.not_applicable_rules:
        output += f"✗ {rule}\n"

    output += "\n## SPECIFIC GUIDANCE:\n\n"

    # Add specific guidance
    for guidance in page_rules.specific_guidance:
        output += f"• {guidance}\n"

    return output
