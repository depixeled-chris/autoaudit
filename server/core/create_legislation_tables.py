"""One-time script to create legislation system tables."""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables(db_path: str = "/app/data/compliance.db"):
    """Create all legislation system tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    logger.info("Creating legislation system tables...")

    # 1. Page types table
    logger.info("Creating page_types table")
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

    # Insert page types
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
            INSERT OR IGNORE INTO page_types
            (code, name, description, preamble, requires_llm_visual_confirmation, requires_human_confirmation, active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (code, name, description, preamble, requires_llm, requires_human))

    logger.info(f"Inserted {len(page_types)} page types")

    # 2. States table
    logger.info("Creating states table")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO states (code, name, active)
        VALUES ('OK', 'Oklahoma', 1)
    """)

    logger.info("Created states table")

    # 3. Legislation sources table
    logger.info("Creating legislation_sources table")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS legislation_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_code TEXT NOT NULL,
            statute_number TEXT NOT NULL,
            title TEXT NOT NULL,
            full_text TEXT NOT NULL,
            source_url TEXT,
            effective_date DATE,
            sunset_date DATE,
            last_verified_date DATE,
            applies_to_page_types TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (state_code) REFERENCES states(code),
            UNIQUE(state_code, statute_number)
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_legislation_sources_state ON legislation_sources(state_code)")

    logger.info("Created legislation_sources table")

    # 4. Legislation digests table
    logger.info("Creating legislation_digests table")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS legislation_digests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            legislation_source_id INTEGER NOT NULL,
            digest_type TEXT NOT NULL CHECK(digest_type IN ('universal', 'page_specific')),
            page_type_code TEXT,
            interpreted_requirements TEXT,
            created_by INTEGER,
            reviewed_by INTEGER,
            last_review_date TIMESTAMP,
            approved BOOLEAN DEFAULT 0,
            version INTEGER DEFAULT 1,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (legislation_source_id) REFERENCES legislation_sources(id),
            FOREIGN KEY (page_type_code) REFERENCES page_types(code)
        )
    """)

    # Unique index: only one active digest per source
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_digest_per_source
        ON legislation_digests(legislation_source_id, active)
        WHERE active = 1
    """)

    logger.info("Created legislation_digests table")

    # 5. Rules table
    logger.info("Creating rules table")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_code TEXT NOT NULL,
            legislation_source_id INTEGER,
            legislation_digest_id INTEGER,
            rule_text TEXT NOT NULL,
            original_rule_text TEXT,
            applies_to_page_types TEXT,
            active INTEGER DEFAULT 1,
            approved INTEGER DEFAULT 0,
            is_manually_modified BOOLEAN DEFAULT 0,
            status TEXT DEFAULT 'active',
            supersedes_rule_id INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (state_code) REFERENCES states(code),
            FOREIGN KEY (legislation_source_id) REFERENCES legislation_sources(id) ON DELETE CASCADE,
            FOREIGN KEY (legislation_digest_id) REFERENCES legislation_digests(id)
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rules_state_code ON rules(state_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rules_legislation_source ON rules(legislation_source_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rules_legislation_digest ON rules(legislation_digest_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rules_active ON rules(active)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rules_approved ON rules(approved)")

    logger.info("Created rules table")

    # 6. Rule collisions table
    logger.info("Creating rule_collisions table")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rule_collisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id INTEGER NOT NULL,
            collides_with_rule_id INTEGER NOT NULL,
            collision_type TEXT NOT NULL CHECK(
                collision_type IN ('duplicate', 'semantic', 'conflict', 'overlap', 'supersedes')
            ),
            confidence REAL,
            ai_explanation TEXT,
            resolution TEXT CHECK(
                resolution IS NULL OR
                resolution IN ('keep_both', 'keep_existing', 'keep_new', 'merge', 'pending')
            ),
            resolved_by INTEGER,
            resolved_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (rule_id) REFERENCES rules(id) ON DELETE CASCADE,
            FOREIGN KEY (collides_with_rule_id) REFERENCES rules(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_collisions_by_rule ON rule_collisions(rule_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_collisions_by_existing ON rule_collisions(collides_with_rule_id)")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_collisions_pending
        ON rule_collisions(resolution)
        WHERE resolution IS NULL OR resolution = 'pending'
    """)

    logger.info("Created rule_collisions table")

    # 7. LLM logs table
    logger.info("Creating llm_logs table")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS llm_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_endpoint TEXT NOT NULL,
            operation_type TEXT NOT NULL,
            user_id INTEGER,
            model TEXT NOT NULL,
            provider TEXT DEFAULT 'openai',
            input_text TEXT NOT NULL,
            output_text TEXT NOT NULL,
            input_tokens INTEGER NOT NULL,
            output_tokens INTEGER NOT NULL,
            total_tokens INTEGER NOT NULL,
            input_cost_usd REAL,
            output_cost_usd REAL,
            total_cost_usd REAL,
            duration_ms INTEGER,
            status TEXT NOT NULL DEFAULT 'success' CHECK(
                status IN ('success', 'error', 'timeout')
            ),
            error_message TEXT,
            request_id TEXT,
            related_entity_type TEXT,
            related_entity_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes
    indexes = [
        ("idx_llm_logs_endpoint", "api_endpoint"),
        ("idx_llm_logs_operation", "operation_type"),
        ("idx_llm_logs_model", "model"),
        ("idx_llm_logs_created", "created_at"),
        ("idx_llm_logs_user", "user_id"),
        ("idx_llm_logs_cost", "total_cost_usd"),
        ("idx_llm_logs_status", "status"),
    ]

    for index_name, column_name in indexes:
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS {index_name}
            ON llm_logs({column_name})
        """)

    logger.info("Created llm_logs table")

    conn.commit()
    conn.close()

    logger.info("✅ All tables created successfully!")


if __name__ == "__main__":
    create_tables()
