"""Configuration settings for the auto dealership compliance checker."""

from typing import Dict, List
from pydantic import BaseModel


class StateRules(BaseModel):
    """State-specific compliance rules."""
    state: str
    required_disclosures: List[str]
    pricing_rules: List[str]
    financing_rules: List[str]


# Sample state rules - expand this based on actual regulations
STATE_REGULATIONS: Dict[str, StateRules] = {
    "CA": StateRules(
        state="California",
        required_disclosures=[
            "Vehicle history report availability",
            "Smog certification status",
            "Lemon law buyback disclosure",
            "Advertised price must include all dealer-imposed fees except government fees",
        ],
        pricing_rules=[
            "Must disclose documentary fees separately",
            "No misleading 'discount' claims without substantiation",
            "Sales tax must be clearly stated or excluded from advertised price",
        ],
        financing_rules=[
            "APR must be disclosed if financing terms mentioned",
            "Down payment requirements must be clearly stated",
            "Total cost of financing must be calculable from advertisement",
        ],
    ),
    "TX": StateRules(
        state="Texas",
        required_disclosures=[
            "Inventory tax disclosure for used vehicles",
            "Title status (clean, salvage, rebuilt)",
            "Odometer reading accuracy statement",
        ],
        pricing_rules=[
            "Out-the-door pricing requirements for online ads",
            "Documentary fee limits and disclosure",
        ],
        financing_rules=[
            "Truth in lending disclosures required",
            "Buy here pay here specific requirements",
        ],
    ),
    "NY": StateRules(
        state="New York",
        required_disclosures=[
            "Lemon law coverage information",
            "Vehicle history availability",
            "Warranty information (new and used)",
        ],
        pricing_rules=[
            "All mandatory fees must be disclosed",
            "No bait-and-switch advertising",
        ],
        financing_rules=[
            "Interest rate disclosure requirements",
            "Payment terms clarity",
        ],
    ),
    "OK": StateRules(
        state="Oklahoma",
        required_disclosures=[
            "Vehicle identification (year, make, model) must be conspicuously disclosed adjacent to price (465:15-3-8)",
            "Stock number required for single vehicle ads, or quantity disclosure for multiple vehicles (465:15-3-2)",
            "Prior service disclosure required (demonstrator, service loaner, factory program vehicle, etc.) (465:15-3-8(a)(4))",
            "Dealership name must be conspicuously displayed in all advertisements (465:15-3-15)",
            "Lease advertisements must clearly disclose the word 'lease' (465:15-3-12)",
            "Number of vehicles available for advertised price must be disclosed (465:15-3-2)",
            "TV/video disclosures must appear continuously for minimum 10 seconds (465:15-1-2)",
            "Vehicles must be in possession or obtainable from manufacturer with disclosure (465:15-3-2)",
            "Illustration must be of actual vehicle or same make/model/year/style (465:15-3-8(b))",
        ],
        pricing_rules=[
            "Most conspicuous price must be full selling price (only excluding tax, title, license) (465:15-3-7(a))",
            "No price qualifications like 'with trade', 'with acceptable trade', 'with dealer-arranged financing' (465:15-3-7(b))",
            "Rebates or incentives included in price must be clearly disclosed (465:15-3-7(c))",
            "Select consumer rebates must be shown separately or clearly identified (465:15-3-7(d))",
            "No bait-and-switch advertising (465:15-3-4)",
            "Savings claims only allowed from MSRP sticker price, not including Monroney discounts (465:15-3-14(5))",
            "Terms 'up to', 'as much as', 'from' prohibited with savings claims unless stock number provided (465:15-3-14(5))",
            "Prohibited: 'dealer's cost', 'invoice', 'invoice price' terminology (465:15-3-14(7))",
            "No trade-in amounts or ranges in advertisements (465:15-3-14(8))",
            "Prohibited: 'we pay tag, tax and license' or similar statements (465:15-3-14(10))",
            "No 'free' or 'complimentary' offers requiring purchase (465:15-3-14(6))",
            "MSRP cannot be inflated or misrepresented (465:15-3-6)",
            "No misleading layouts, headlines, or type sizes (465:15-3-5)",
            "Used vehicles cannot be advertised as new (465:15-3-14(9))",
            "Terms like 'factory direct prices', 'wholesale prices' prohibited (465:15-3-14(4))",
            "No claims about exclusive arrangements not available to other dealers (465:15-3-14(4))",
            "No false claims about trade-in allowances compared to competitors (465:15-3-14(2))",
            "No false claims about volume purchasing advantages (465:15-3-14(3))",
            "'Liquidation', 'going out of business' only if actually closing (465:15-3-14(11))",
        ],
        financing_rules=[
            "Must comply with FTC Regulation M (Lease Regulation) (465:15-3-13)",
            "Must comply with FTC Regulation Z (Truth in Lending Act) (465:15-3-13)",
            "Prohibited: 'everybody financed', 'no credit rejected', 'guaranteed approval' (465:15-3-14(1))",
            "Buy-down rates require disclaimer about effect on vehicle price (465:15-3-14(12))",
            "'We will pay off your trade' requires disclosure that amount is added to contract (465:15-3-14(13))",
            "Payment deferral claims must match actual finance contract terms (465:15-3-14(14))",
            "Lease terms not available to general public cannot be in general ads (465:15-3-12)",
            "All lease limitations and qualifications must be clearly disclosed (465:15-3-12)",
            "Statements like 'alternative financial plan' without 'lease' are inadequate (465:15-3-12)",
        ],
    ),
}


# LLM Configuration
OPENAI_MODEL = "gpt-4.1-nano"  # GPT-4.1 Nano for fast, cost-effective compliance checking
MAX_TOKENS = 4000
TEMPERATURE = 0.1  # Low temperature for consistent compliance checking


# Scraping Configuration
SCRAPING_TIMEOUT = 60000  # 60 seconds
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


# Environment Configuration
import os

DATABASE_PATH = os.getenv("DATABASE_PATH", "compliance.db")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
