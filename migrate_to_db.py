"""Migration script to move JSON templates to SQLite database."""

import json
from pathlib import Path
import logging
from database import ComplianceDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_compliance_templates(db: ComplianceDatabase, templates_dir: str = "templates"):
    """
    Migrate compliance templates from JSON files to database.

    Args:
        db: Database instance
        templates_dir: Directory containing template JSON files
    """
    templates_path = Path(templates_dir)
    if not templates_path.exists():
        logger.info(f"No templates directory found at {templates_dir}")
        return

    json_files = list(templates_path.glob("*.json"))
    if not json_files:
        logger.info("No template JSON files found")
        return

    logger.info(f"Found {len(json_files)} template files to migrate")

    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                config = json.load(f)

            template_id = config.get('template_id')
            if not template_id:
                logger.warning(f"Skipping {json_file.name}: No template_id found")
                continue

            # Save template
            platform = config.get('platform', 'unknown')
            db.save_template(template_id, platform, config)
            logger.info(f"Migrated template: {template_id}")

            # Save rules
            known_compliance = config.get('known_compliance', {})
            for rule_key, rule_data in known_compliance.items():
                db.save_template_rule(
                    template_id=template_id,
                    rule_key=rule_key,
                    status=rule_data.get('status', 'unknown'),
                    confidence=rule_data.get('confidence', 0.0),
                    verification_method=rule_data.get('verification_method', 'unknown'),
                    notes=rule_data.get('notes', '')
                )
                logger.info(f"  - Migrated rule: {rule_key}")

        except Exception as e:
            logger.error(f"Error migrating {json_file.name}: {str(e)}")


def migrate_extraction_templates(db: ComplianceDatabase, templates_dir: str = "extraction_templates"):
    """
    Migrate extraction templates from JSON files to database.

    Args:
        db: Database instance
        templates_dir: Directory containing extraction template JSON files
    """
    templates_path = Path(templates_dir)
    if not templates_path.exists():
        logger.info(f"No extraction templates directory found at {templates_dir}")
        return

    json_files = list(templates_path.glob("*.json"))
    if not json_files:
        logger.info("No extraction template JSON files found")
        return

    logger.info(f"Found {len(json_files)} extraction template files to migrate")

    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                config = json.load(f)

            template_id = config.get('template_id')
            if not template_id:
                logger.warning(f"Skipping {json_file.name}: No template_id found")
                continue

            # Save extraction template
            db.save_extraction_template(
                template_id=template_id,
                platform=config.get('platform', 'unknown'),
                selectors=config.get('selectors', {}),
                cleanup_rules=config.get('cleanup_rules', {}),
                extraction_order=config.get('extraction_order', [])
            )
            logger.info(f"Migrated extraction template: {template_id}")

        except Exception as e:
            logger.error(f"Error migrating {json_file.name}: {str(e)}")


def create_sample_project(db: ComplianceDatabase):
    """Create a sample project with some URLs."""
    try:
        # Check if project already exists
        existing = db.get_project(name="AllStar CDJR Muskogee")
        if existing:
            logger.info("Sample project already exists")
            return existing['id']

        project_id = db.create_project(
            name="AllStar CDJR Muskogee",
            state_code="OK",
            description="Oklahoma dealership compliance monitoring"
        )
        logger.info(f"Created sample project: AllStar CDJR Muskogee (ID: {project_id})")

        # Add some sample URLs
        db.add_url(
            url="https://www.allstarcdjrmuskogee.com/used/Chevrolet/2022-Chevrolet-Silverado-1500-f793dc61ac184236e10863afe4bf9621.htm",
            project_id=project_id,
            url_type="vdp",
            template_id="dealer.com_vdp",
            platform="dealer.com",
            check_frequency_hours=24
        )
        logger.info("Added sample URL")

        return project_id

    except Exception as e:
        logger.error(f"Error creating sample project: {str(e)}")
        return None


def main():
    """Run migration."""
    logger.info("=" * 80)
    logger.info("MIGRATION: JSON Templates -> SQLite Database")
    logger.info("=" * 80)

    # Initialize database
    db = ComplianceDatabase("compliance.db")
    logger.info("Database initialized")

    # Migrate compliance templates
    logger.info("\n--- Migrating Compliance Templates ---")
    migrate_compliance_templates(db, "templates")

    # Migrate extraction templates
    logger.info("\n--- Migrating Extraction Templates ---")
    migrate_extraction_templates(db, "extraction_templates")

    # Create sample project
    logger.info("\n--- Creating Sample Project ---")
    project_id = create_sample_project(db)

    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("MIGRATION COMPLETE")
    logger.info("=" * 80)

    if project_id:
        summary = db.get_project_summary(project_id)
        logger.info(f"\nProject Summary:")
        logger.info(f"  Total URLs: {summary['total_urls']}")
        logger.info(f"  Total Checks: {summary['total_checks']}")
        logger.info(f"  Average Score: {summary['avg_score']}")
        logger.info(f"  Total Violations: {summary['total_violations']}")

    # List templates
    logger.info("\nDatabase Contents:")
    logger.info(f"  Projects: {len(db.list_projects())}")

    db.close()
    logger.info("\nDatabase migration successful!")


if __name__ == "__main__":
    main()
