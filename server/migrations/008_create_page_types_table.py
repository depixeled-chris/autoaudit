"""Create page_types table to track all page type configurations."""

import sqlite3


def up(conn: sqlite3.Connection):
    """Apply migration."""
    cursor = conn.cursor()

    # Create page_types table with all fields
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS page_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            description TEXT,
            active BOOLEAN DEFAULT 1,
            preamble TEXT,
            extraction_template TEXT,
            requires_llm_visual_confirmation BOOLEAN DEFAULT 0,
            requires_human_confirmation BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert all page types with preambles and settings
    page_types = [
        ('HOMEPAGE', 'Homepage', 'Dealership homepage/landing page',
         'Analyze this homepage for automotive dealership advertising compliance. Focus on disclosure requirements, font sizes, and layout positioning.',
         1, 0),
        ('VDP', 'Vehicle Detail Page', 'Individual vehicle listing page',
         'Analyze this Vehicle Detail Page (VDP) for compliance. Pay special attention to pricing disclosures, finance terms, and required disclaimers.',
         1, 0),
        ('INVENTORY', 'Inventory Listing', 'Vehicle inventory search/browse page',
         'Analyze this inventory listing page for compliance. Check that all vehicles display required disclosures consistently.',
         0, 0),
        ('SRP', 'Search Results Page', 'Search results for vehicles',
         'Analyze this search results page for compliance. Verify that all listed vehicles include proper disclosures.',
         0, 0),
        ('SPECIALS', 'Special Offers', 'Special offers and promotions page',
         'Analyze this special offers page for compliance. Pay close attention to pricing claims, limited-time offers, and required disclosures for promotional content.',
         1, 0),
        ('FINANCING', 'Financing', 'Finance and payment calculator pages',
         'Analyze this financing page for compliance. Focus on APR disclosures, finance terms, payment calculations, and state-specific finance disclosure requirements.',
         1, 1),
        ('LEASE', 'Lease Offers', 'Lease offer and calculator pages',
         'Analyze this lease offer page for compliance. Verify monthly payment disclosures, lease terms, mileage limitations, and required lease advertising disclaimers.',
         1, 1),
        ('SERVICE', 'Service', 'Service department pages',
         'Analyze this service page for compliance. Check pricing claims for service packages, warranty statements, and service-related disclaimers.',
         0, 0),
        ('PARTS', 'Parts', 'Parts department pages',
         'Analyze this parts page for compliance. Verify pricing claims, availability statements, and OEM vs aftermarket part disclosures.',
         0, 0),
        ('ABOUT', 'About Us', 'About us and dealership information',
         'Analyze this about page for compliance. Check for awards/certifications that require validation and any business practice claims.',
         0, 0),
        ('CONTACT', 'Contact', 'Contact and location pages',
         'Analyze this contact page for compliance. Verify hours of operation claims and location information accuracy.',
         0, 0),
        ('TESTIMONIALS', 'Testimonials', 'Customer reviews and testimonials',
         'Analyze this testimonials page for compliance with FTC regulations. Verify testimonials are genuine, properly disclosed, and meet verification requirements.',
         0, 0),
        ('NEW_INVENTORY', 'New Inventory', 'New vehicle inventory listing',
         'Analyze this new vehicle inventory page for compliance. Focus on MSRP vs dealer pricing disclosures, manufacturer incentives, and new vehicle advertising requirements.',
         1, 0),
        ('USED_INVENTORY', 'Used Inventory', 'Used vehicle inventory listing',
         'Analyze this used vehicle inventory page for compliance. Check vehicle history disclosures, as-is vs warranty statements, and used vehicle advertising requirements.',
         1, 0),
        ('CPO', 'Certified Pre-Owned', 'Certified pre-owned inventory',
         'Analyze this certified pre-owned page for compliance. Verify certification disclosures, warranty information prominence, and CPO program requirements.',
         1, 1),
        ('TRADE_IN', 'Trade-In', 'Trade-in value and calculator pages',
         'Analyze this trade-in page for compliance. Check valuation claims, conditional offer language, and required disclaimers for trade-in estimates.',
         0, 0),
        ('APPRAISAL', 'Appraisal', 'Vehicle appraisal pages',
         'Analyze this appraisal page for compliance. Verify appraisal claims, estimate disclaimers, and conditional language requirements.',
         0, 0),
        ('WARRANTIES', 'Warranties', 'Extended warranty and protection plans',
         'Analyze this warranty page for compliance. Focus on detailed disclosure requirements, terms and conditions prominence, and warranty claim limitations.',
         0, 1),
    ]

    for code, name, description, preamble, requires_llm, requires_human in page_types:
        cursor.execute("""
            INSERT INTO page_types
            (code, name, description, preamble, requires_llm_visual_confirmation, requires_human_confirmation, active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (code, name, description, preamble, requires_llm, requires_human))

    conn.commit()


def down(conn: sqlite3.Connection):
    """Revert migration."""
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS page_types")
    conn.commit()
