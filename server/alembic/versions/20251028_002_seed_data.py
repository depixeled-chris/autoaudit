"""Insert essential seed data

Revision ID: 20251028_002
Revises: 20251028_001
Create Date: 2025-10-28

Inserts essential seed data required for application operation:
- Oklahoma state (can add more states later)
- 5 LLM model config entries (operation type mappings)
- 18 page types (HOMEPAGE, VDP, INVENTORY, FINANCING, etc.)
- 1 preamble template (Standard Hierarchical)

This migration is idempotent - it won't re-insert if data already exists.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision: str = '20251028_002'
down_revision: Union[str, None] = '20251028_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Insert seed data."""
    conn = op.get_bind()

    # Check if seed data already exists
    result = conn.execute(text("SELECT COUNT(*) FROM states"))
    state_count = result.scalar()

    if state_count > 0:
        print("⚠️  Seed data already exists - skipping insertion")
        return

    print("✓ Inserting seed data...")

    # Insert Oklahoma state
    conn.execute(text("""
        INSERT INTO states (id, code, name, active, created_at, updated_at)
        VALUES (1, 'OK', 'Oklahoma', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """))

    # Insert LLM model config
    conn.execute(text("""
        INSERT INTO llm_model_config (operation_type, model, description, created_at, updated_at) VALUES
        ('PARSE_LEGISLATION', 'gpt-4o-mini', 'Parse uploaded legislation documents into structured data', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('GENERATE_RULES', 'gpt-4o-mini', 'Generate atomic compliance rules from legislation', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('DETECT_COLLISIONS', 'gpt-4o-mini', 'Detect semantic collisions between rules', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('GENERATE_PREAMBLE', 'gpt-4o-mini', 'Generate page-specific preambles', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('COMPLIANCE_CHECK', 'gpt-4o-mini', 'Check URL compliance against rules', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """))

    # Insert page types
    page_types = [
        ('HOMEPAGE', 'Homepage', 'Dealership homepage/landing page',
         'Analyze this homepage for automotive dealership advertising compliance. Focus on disclosure requirements, font sizes, and layout positioning.', 1, 0),
        ('VDP', 'Vehicle Detail Page', 'Individual vehicle listing page',
         'Analyze this Vehicle Detail Page (VDP) for compliance. Pay special attention to pricing disclosures, finance terms, and required disclaimers.', 1, 0),
        ('INVENTORY', 'Inventory Listing', 'Vehicle inventory search/browse page',
         'Analyze this inventory listing page for compliance. Check that all vehicles display required disclosures consistently.', 0, 0),
        ('SRP', 'Search Results Page', 'Search results for vehicles',
         'Analyze this search results page for compliance. Verify that all listed vehicles include proper disclosures.', 0, 0),
        ('SPECIALS', 'Special Offers', 'Special offers and promotions page',
         'Analyze this special offers page for compliance. Pay close attention to pricing claims, limited-time offers, and required disclosures for promotional content.', 1, 0),
        ('FINANCING', 'Financing', 'Finance and payment calculator pages',
         'Analyze this financing page for compliance. Focus on APR disclosures, finance terms, payment calculations, and state-specific finance disclosure requirements.', 1, 1),
        ('LEASE', 'Lease Offers', 'Lease offer and calculator pages',
         'Analyze this lease offer page for compliance. Verify monthly payment disclosures, lease terms, mileage limitations, and required lease advertising disclaimers.', 1, 1),
        ('SERVICE', 'Service', 'Service department pages',
         'Analyze this service page for compliance. Check pricing claims for service packages, warranty statements, and service-related disclaimers.', 0, 0),
        ('PARTS', 'Parts', 'Parts department pages',
         'Analyze this parts page for compliance. Verify pricing claims, availability statements, and OEM vs aftermarket part disclosures.', 0, 0),
        ('ABOUT', 'About Us', 'About us and dealership information',
         'Analyze this about page for compliance. Check for awards/certifications that require validation and any business practice claims.', 0, 0),
        ('CONTACT', 'Contact', 'Contact and location pages',
         'Analyze this contact page for compliance. Verify hours of operation claims and location information accuracy.', 0, 0),
        ('TESTIMONIALS', 'Testimonials', 'Customer reviews and testimonials',
         'Analyze this testimonials page for compliance with FTC regulations. Verify testimonials are genuine, properly disclosed, and meet verification requirements.', 0, 0),
        ('NEW_INVENTORY', 'New Inventory', 'New vehicle inventory listing',
         'Analyze this new vehicle inventory page for compliance. Focus on MSRP vs dealer pricing disclosures, manufacturer incentives, and new vehicle advertising requirements.', 1, 0),
        ('USED_INVENTORY', 'Used Inventory', 'Used vehicle inventory listing',
         'Analyze this used vehicle inventory page for compliance. Check vehicle history disclosures, as-is vs warranty statements, and used vehicle advertising requirements.', 1, 0),
        ('CPO', 'Certified Pre-Owned', 'Certified pre-owned inventory',
         'Analyze this certified pre-owned page for compliance. Verify certification disclosures, warranty information prominence, and CPO program requirements.', 1, 1),
        ('TRADE_IN', 'Trade-In', 'Trade-in value and calculator pages',
         'Analyze this trade-in page for compliance. Check valuation claims, conditional offer language, and required disclaimers for trade-in estimates.', 0, 0),
        ('APPRAISAL', 'Appraisal', 'Vehicle appraisal pages',
         'Analyze this appraisal page for compliance. Verify appraisal claims, estimate disclaimers, and conditional language requirements.', 0, 0),
        ('WARRANTIES', 'Warranties', 'Extended warranty and protection plans',
         'Analyze this warranty page for compliance. Focus on detailed disclosure requirements, terms and conditions prominence, and warranty claim limitations.', 0, 1),
    ]

    for code, name, description, preamble, llm_visual, human_confirm in page_types:
        conn.execute(text("""
            INSERT INTO page_types
            (code, name, description, preamble, requires_llm_visual_confirmation, requires_human_confirmation, active, created_at, updated_at)
            VALUES (:code, :name, :description, :preamble, :llm_visual, :human_confirm, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """), {
            'code': code,
            'name': name,
            'description': description,
            'preamble': preamble,
            'llm_visual': llm_visual,
            'human_confirm': human_confirm
        })

    # Insert preamble template
    template_structure = '''# UNIVERSAL COMPLIANCE PRINCIPLES
{{ universal_preamble }}

# STATE-SPECIFIC REQUIREMENTS: {{ state_code }}
{{ state_preamble }}

# PAGE TYPE GUIDANCE: {{ page_type }}
{{ page_type_preamble }}

{% if project_preamble %}
# PROJECT-SPECIFIC CONTEXT
{{ project_preamble }}
{% endif %}

# CITATION FORMAT REQUIREMENTS
CRITICAL: Format all citations as structured JSON:
{
  "violations": [
    {
      "statute": "Full statute reference",
      "rule": "Plain language requirement",
      "severity": "critical|important|minor",
      "location": "Where violation occurs",
      "evidence": "Specific violating content",
      "recommendation": "How to fix"
    }
  ]
}'''

    conn.execute(text("""
        INSERT INTO preamble_templates (name, description, template_structure, is_default, created_at, updated_at)
        VALUES (
            'Standard Hierarchical',
            'Standard composition: Universal → State → Page Type → Project',
            :template_structure,
            1,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        )
    """), {'template_structure': template_structure})

    conn.commit()
    print("✓ Inserted seed data: 1 state, 5 LLM configs, 18 page types, 1 preamble template")


def downgrade() -> None:
    """Remove seed data."""
    conn = op.get_bind()

    conn.execute(text("DELETE FROM preamble_templates WHERE name = 'Standard Hierarchical'"))
    conn.execute(text("DELETE FROM page_types"))
    conn.execute(text("DELETE FROM llm_model_config"))
    conn.execute(text("DELETE FROM states WHERE code = 'OK'"))

    conn.commit()
    print("✓ Removed seed data")
