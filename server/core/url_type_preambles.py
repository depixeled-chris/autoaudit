"""URL type-specific preambles for compliance analysis.

Different page types have different compliance expectations and focus areas.
"""

from typing import Dict

# URL type-specific analysis preambles
URL_TYPE_PREAMBLES: Dict[str, Dict[str, str]] = {
    "VDP": {
        "name": "Vehicle Detail Page",
        "description": "Individual vehicle listing page showing a specific car for sale",
        "preamble": """
This is a **Vehicle Detail Page (VDP)** - a page showing a specific vehicle for sale.

## Analysis Focus for VDP Pages:

**Primary Compliance Areas:**
1. **Price Disclosure**:
   - Price must be clearly displayed
   - All fees and charges must be disclosed near the price
   - Final/total price must be clear vs. advertised/sale price
   - Any price qualifications must be conspicuous

2. **Vehicle Identification**:
   - Year, make, model must be clearly associated with the price
   - VIN or stock number should be present
   - Mileage disclosure
   - Trim level and major features

3. **Disclaimers & Disclosures**:
   - Financing disclaimers (if financing advertised)
   - Rebate/incentive disclaimers
   - Tax, title, license disclaimers
   - Any condition disclaimers (certified, pre-owned, etc.)

4. **Visual Proximity**:
   - Vehicle identification must be visually adjacent to pricing
   - Disclaimers must be reasonably associated with claims
   - Contact information should be accessible

**What NOT to flag on VDP pages:**
- Missing inventory-level features (filtering, sorting, etc.)
- Homepage requirements (general dealer info can be in footer/nav)
- Lack of multiple vehicle comparisons

**Interpretation Guidance:**
- Vehicle info in page title/heading above price section = adjacent
- Footer disclaimers are acceptable for standard regulatory text
- Focus on preventing consumer confusion about THAT specific vehicle
"""
    },

    "INVENTORY": {
        "name": "Inventory List Page",
        "description": "Page showing multiple vehicles, typically with filtering/sorting",
        "preamble": """
This is an **Inventory List/Search Page** - a page showing multiple vehicles available for sale.

## Analysis Focus for Inventory Pages:

**Primary Compliance Areas:**
1. **Consistent Price Display**:
   - All vehicles should show pricing consistently
   - If one vehicle shows "Call for Price", all should (or none should)
   - Price format should be uniform across listings

2. **Bulk Disclosure Requirements**:
   - General disclaimer about prices, fees, taxes visible on page
   - "Prices exclude tax, title, license" or similar
   - Any rebate/incentive qualifications that apply to multiple vehicles

3. **Vehicle Identification in Listings**:
   - Each listing should show year, make, model
   - Mileage should be visible
   - Stock number or VIN if shown should be consistent

4. **Filtering & Search Functionality**:
   - Price range filters should be accurate
   - Search/filter controls should work as labeled
   - Sorting options should be clear

**What NOT to flag on Inventory pages:**
- Individual vehicle detail requirements (those apply to VDP)
- Detailed disclaimers for each vehicle (general page disclaimers are sufficient)
- Lack of full vehicle specifications (that's for VDP)
- Missing full financing terms (general availability is enough)

**Interpretation Guidance:**
- General disclaimers at top or bottom of inventory list are acceptable
- Focus on consistency across listings, not perfection for each one
- "See dealer for details" is acceptable when showing many vehicles
- Price transparency across the board is more important than individual detail
"""
    },

    "HOMEPAGE": {
        "name": "Homepage",
        "description": "Main dealership homepage or landing page",
        "preamble": """
This is a **Homepage or Landing Page** - the main entry point to the dealership website.

## Analysis Focus for Homepage:

**Primary Compliance Areas:**
1. **Dealership Identity & Contact**:
   - Dealership name clearly displayed
   - Physical address visible (header, footer, or contact section)
   - Phone number accessible
   - Business hours if mentioned

2. **General Advertising Claims**:
   - Any promotional claims must be substantiated or qualified
   - "Best prices", "Lowest rates" need disclaimers
   - Limited-time offers should show expiration
   - Special financing claims need general disclaimers

3. **Featured Vehicle Compliance**:
   - If specific vehicles are featured, basic compliance applies
   - Price + vehicle ID if price is shown
   - General disclaimers for promotional offers

4. **Legal & Regulatory Disclosures**:
   - Licensing information (if required by state)
   - Equal housing/opportunity statements if applicable
   - Privacy policy accessible

**What NOT to flag on Homepage:**
- Detailed vehicle-level compliance (that's for VDP/Inventory)
- Missing individual VIN numbers
- Lack of detailed financing terms for promotional offers
- Navigation/usability issues unless compliance-related

**Interpretation Guidance:**
- Homepage can link to detail pages rather than showing everything
- General "see dealer for details" is often acceptable
- Focus on preventing misleading advertising, not cataloging information
- Footer disclosures are standard and acceptable for homepages
- Contact info can be in header, footer, or dedicated "Contact" page
"""
    },

    "ABOUT": {
        "name": "About/Info Page",
        "description": "Page providing information about the dealership, services, or policies",
        "preamble": """
This is an **About/Information Page** - providing dealership information, services, or policies.

## Analysis Focus for About Pages:

**Primary Compliance Areas:**
1. **Accurate Representation**:
   - Claims about dealership must be truthful
   - Service offerings must be accurate
   - Certifications/awards must be legitimate and current

2. **Contact & Location Information**:
   - Address should be accurate
   - Contact methods should work
   - Hours of operation should be current

3. **Service Claims**:
   - Any guarantees or warranties must be properly qualified
   - Service pricing claims need disclaimers
   - Promotional service offers need terms

**What NOT to flag on About pages:**
- Vehicle pricing details (not applicable)
- Inventory-specific requirements
- Individual vehicle compliance

**Interpretation Guidance:**
- These pages are informational, not transactional
- Focus on preventing false claims about the business itself
- General statements like "best service" are acceptable puffery
- Specific measurable claims need substantiation
"""
    },

    "SPECIALS": {
        "name": "Specials/Promotions Page",
        "description": "Page showing current deals, promotions, or special offers",
        "preamble": """
This is a **Specials/Promotions Page** - showcasing current deals and offers.

## Analysis Focus for Specials Pages:

**Primary Compliance Areas:**
1. **Offer Terms & Conditions**:
   - Clear expiration dates for limited-time offers
   - Qualification requirements clearly stated
   - Material terms disclosed (down payment, term length, etc.)
   - Availability disclaimers (while supplies last, etc.)

2. **Pricing Disclosures**:
   - If specific prices shown, must include disclaimers
   - Rebates/incentives must show qualification requirements
   - Financing terms must show APR, term, conditions
   - Monthly payment ads must include full disclosure

3. **Featured Vehicle Compliance**:
   - Vehicles shown in specials need basic identification
   - Stock numbers/availability must be clear
   - Photos must represent actual available vehicles (or disclaim stock photos)

4. **Misleading Claims**:
   - "Guaranteed approval" must be qualified
   - "Lowest price" must be substantiated
   - Comparison claims need basis/disclaimers

**What NOT to flag on Specials pages:**
- Detailed individual VDP compliance (unless specific vehicle featured)
- General inventory requirements
- Detailed service specifications

**Interpretation Guidance:**
- Disclaimers can be near the offer or at page bottom
- "See dealer for details" is acceptable for complex programs
- Material terms should be visible, not hidden
- Focus on preventing deceptive advertising
"""
    },

    "SERVICE": {
        "name": "Service Department Page",
        "description": "Page about service department, maintenance, or repairs",
        "preamble": """
This is a **Service Department Page** - about maintenance, repairs, and service offerings.

## Analysis Focus for Service Pages:

**Primary Compliance Areas:**
1. **Service Pricing**:
   - Advertised prices must include qualifications
   - Coupons must show expiration and terms
   - "Starting at" prices need clear disclosure
   - Package deals must show what's included/excluded

2. **Service Claims**:
   - Warranty claims must be accurate
   - "Certified technician" claims must be substantiated
   - Equipment/capability claims must be truthful
   - Turnaround time claims must be reasonable

3. **Promotional Offers**:
   - Service specials need clear terms
   - Discounts must show original price or value
   - Free service claims must show conditions
   - First-time customer offers need clear definition

**What NOT to flag on Service pages:**
- Vehicle sales pricing (not applicable)
- Inventory requirements
- VDP compliance

**Interpretation Guidance:**
- Service pages are separate from vehicle sales compliance
- Focus on preventing service deception
- General claims about quality are acceptable puffery
- Specific measurable claims need backing
"""
    },

    "FINANCING": {
        "name": "Financing/Credit Page",
        "description": "Page about financing options, credit applications, or payment calculators",
        "preamble": """
This is a **Financing/Credit Page** - about financing options and credit applications.

## Analysis Focus for Financing Pages:

**Primary Compliance Areas:**
1. **APR & Rate Disclosures**:
   - Advertised rates must show APR, not just rate
   - Term length must be disclosed
   - Qualification requirements (credit score, down payment)
   - "Rates as low as" must show best-case scenario basis

2. **Credit Application Compliance**:
   - Privacy policy must be accessible
   - Equal opportunity disclosures
   - Data security information
   - Clear submission terms

3. **Payment Calculator Accuracy**:
   - Must include all required loan terms
   - Must clarify estimates vs. actual offers
   - Must show what's included/excluded from payment
   - Disclaimer about final approval

4. **Misleading Claims**:
   - "Guaranteed approval" must be qualified
   - "Bad credit OK" must be truthful
   - Comparison rates must be valid
   - Pre-approval claims must be accurate

**What NOT to flag on Financing pages:**
- Vehicle-specific pricing (unless example shown)
- Inventory compliance
- Service department requirements

**Interpretation Guidance:**
- Federal Truth in Lending Act (TILA/Reg Z) may apply
- State-specific credit advertising rules apply
- Calculators must be clearly labeled as estimates
- Focus on preventing credit advertising deception
"""
    },
}

def get_preamble(url_type: str) -> str:
    """
    Get the analysis preamble for a specific URL type.

    Args:
        url_type: Type of URL (VDP, INVENTORY, HOMEPAGE, etc.)

    Returns:
        Preamble text to prepend to compliance analysis prompt
    """
    url_type = url_type.upper()

    if url_type not in URL_TYPE_PREAMBLES:
        # Default to VDP if unknown type
        return URL_TYPE_PREAMBLES["VDP"]["preamble"]

    return URL_TYPE_PREAMBLES[url_type]["preamble"]


def get_url_type_name(url_type: str) -> str:
    """Get the human-readable name for a URL type."""
    url_type = url_type.upper()
    return URL_TYPE_PREAMBLES.get(url_type, {}).get("name", url_type)


def get_url_type_description(url_type: str) -> str:
    """Get the description for a URL type."""
    url_type = url_type.upper()
    return URL_TYPE_PREAMBLES.get(url_type, {}).get("description", "")
