"""Add additional page types for comprehensive dealership coverage."""

import sqlite3

def up(conn: sqlite3.Connection):
    """Apply migration."""
    cursor = conn.cursor()

    # Insert new page types
    page_types = [
        # Special offers and promotions
        ('SPECIALS', 'Special Offers', 'Special offers and promotions page',
         'Analyze this special offers page for compliance. Pay close attention to pricing claims, limited-time offers, and required disclosures for promotional content.',
         1, 0),

        # Finance and lease pages
        ('FINANCING', 'Financing', 'Finance and payment calculator pages',
         'Analyze this financing page for compliance. Focus on APR disclosures, finance terms, payment calculations, and state-specific finance disclosure requirements.',
         1, 1),

        ('LEASE', 'Lease Offers', 'Lease offer and calculator pages',
         'Analyze this lease offer page for compliance. Verify monthly payment disclosures, lease terms, mileage limitations, and required lease advertising disclaimers.',
         1, 1),

        # Service and parts
        ('SERVICE', 'Service', 'Service department pages',
         'Analyze this service page for compliance. Check pricing claims for service packages, warranty statements, and service-related disclaimers.',
         0, 0),

        ('PARTS', 'Parts', 'Parts department pages',
         'Analyze this parts page for compliance. Verify pricing claims, availability statements, and OEM vs aftermarket part disclosures.',
         0, 0),

        # Informational pages
        ('ABOUT', 'About Us', 'About us and dealership information',
         'Analyze this about page for compliance. Check for awards/certifications that require validation and any business practice claims.',
         0, 0),

        ('CONTACT', 'Contact', 'Contact and location pages',
         'Analyze this contact page for compliance. Verify hours of operation claims and location information accuracy.',
         0, 0),

        ('TESTIMONIALS', 'Testimonials', 'Customer reviews and testimonials',
         'Analyze this testimonials page for compliance with FTC regulations. Verify testimonials are genuine, properly disclosed, and meet verification requirements.',
         0, 0),

        # Inventory variations
        ('NEW_INVENTORY', 'New Inventory', 'New vehicle inventory listing',
         'Analyze this new vehicle inventory page for compliance. Focus on MSRP vs dealer pricing disclosures, manufacturer incentives, and new vehicle advertising requirements.',
         1, 0),

        ('USED_INVENTORY', 'Used Inventory', 'Used vehicle inventory listing',
         'Analyze this used vehicle inventory page for compliance. Check vehicle history disclosures, as-is vs warranty statements, and used vehicle advertising requirements.',
         1, 0),

        ('CPO', 'Certified Pre-Owned', 'Certified pre-owned inventory',
         'Analyze this certified pre-owned page for compliance. Verify certification disclosures, warranty information prominence, and CPO program requirements.',
         1, 1),

        # Value proposition pages
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
            INSERT OR IGNORE INTO page_types
            (code, name, description, preamble, requires_llm_visual_confirmation, requires_human_confirmation, active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (code, name, description, preamble, requires_llm, requires_human))

    conn.commit()

def down(conn: sqlite3.Connection):
    """Revert migration."""
    cursor = conn.cursor()

    # Remove the newly added page types
    codes = [
        'SPECIALS', 'FINANCING', 'LEASE', 'SERVICE', 'PARTS', 'ABOUT',
        'CONTACT', 'TESTIMONIALS', 'NEW_INVENTORY', 'USED_INVENTORY',
        'CPO', 'TRADE_IN', 'APPRAISAL', 'WARRANTIES'
    ]

    placeholders = ', '.join('?' * len(codes))
    cursor.execute(f"DELETE FROM page_types WHERE code IN ({placeholders})", codes)
    conn.commit()
