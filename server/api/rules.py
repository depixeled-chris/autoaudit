"""API routes for rules management."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict
import logging

from core.database import ComplianceDatabase
from api.dependencies import get_db, get_current_user
from services.rule_service import RuleService
from services.state_service import StateService
from services.document_parser_service import DocumentParserService
from schemas.rule import (
    RuleCreate, RuleUpdate, RuleResponse, RulesListResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rules", tags=["rules"])


# Rule CRUD operations
@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    rule_data: RuleCreate,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Create a new rule."""
    service = RuleService(db)
    try:
        return service.create_rule(rule_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=RulesListResponse)
async def list_rules(
    state_code: Optional[str] = None,
    active_only: bool = False,
    approved_only: bool = False,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    List rules with optional filters.

    - **state_code**: Filter by state (e.g., 'CA', 'TX')
    - **active_only**: Only return active rules
    - **approved_only**: Only return approved rules
    """
    service = RuleService(db)
    rules = service.list_rules(
        state_code=state_code,
        active_only=active_only,
        approved_only=approved_only
    )
    return RulesListResponse(rules=rules, total=len(rules))


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: int,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get a single rule by ID."""
    service = RuleService(db)
    rule = service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.patch("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: int,
    rule_data: RuleUpdate,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Update a rule."""
    service = RuleService(db)

    # Check if rule exists
    existing_rule = service.get_rule(rule_id)
    if not existing_rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    try:
        return service.update_rule(rule_id, rule_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: int,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Delete a rule."""
    service = RuleService(db)

    # Check if rule exists
    existing_rule = service.get_rule(rule_id)
    if not existing_rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    try:
        service.delete_rule(rule_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Bulk operations
@router.delete("/states/{state_code}/rules", response_model=Dict)
async def delete_rules_by_state(
    state_code: str,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Delete all rules for a specific state.
    Use with caution - this is a destructive operation.
    """
    service = RuleService(db)
    try:
        count = service.delete_rules_by_state(state_code)
        return {
            "message": f"Deleted {count} rules for state {state_code}",
            "count": count,
            "state_code": state_code
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Get rules by legislation source
@router.get("/legislation/{source_id}", response_model=RulesListResponse)
async def get_rules_by_legislation(
    source_id: int,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get all rules associated with a specific legislation source.
    This includes rules from all digest versions (active and inactive).
    """
    service = RuleService(db)
    cursor = db.conn.cursor()

    # Get all rules for this legislation source
    cursor.execute("""
        SELECT * FROM rules
        WHERE legislation_source_id = ?
        ORDER BY created_at DESC
    """, (source_id,))

    rows = cursor.fetchall()
    rules = []

    for row in rows:
        rule_dict = dict(zip([col[0] for col in cursor.description], row))
        rules.append(rule_dict)

    return RulesListResponse(rules=rules, total=len(rules))


# Re-digest legislation source into rules
@router.post("/legislation/{source_id}/digest", response_model=Dict, status_code=status.HTTP_201_CREATED)
async def digest_legislation_to_rules(
    source_id: int,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Digest or re-digest a legislation source into rules using LLM.

    **First digest**: Creates new digest and rules
    **Re-digest**: Preserves approved/manually-modified rules, replaces unapproved ones

    Protected rules (approved=1 OR is_manually_modified=1) are NOT deleted.
    """
    logger.info(f"Digesting legislation source {source_id} into rules")

    # Get the legislation source
    state_service = StateService(db)
    legislation_source = state_service.get_legislation_source(source_id)

    if not legislation_source:
        raise HTTPException(status_code=404, detail="Legislation source not found")

    try:
        rule_service = RuleService(db)

        # Get or create legislation digest
        cursor = db.conn.cursor()

        # Check for existing active digest
        cursor.execute("""
            SELECT id, version FROM legislation_digests
            WHERE legislation_source_id = ? AND active = 1
        """, (source_id,))

        existing_digest = cursor.fetchone()

        if existing_digest:
            old_digest_id = existing_digest[0]
            old_version = existing_digest[1]
            new_version = old_version + 1

            # Get protected rules count before deletion
            cursor.execute("""
                SELECT COUNT(*) FROM rules
                WHERE legislation_digest_id = ?
                AND (approved = 1 OR is_manually_modified = 1)
            """, (old_digest_id,))
            protected_count = cursor.fetchone()[0]

            # Mark old digest as inactive
            cursor.execute("""
                UPDATE legislation_digests SET active = 0
                WHERE id = ?
            """, (old_digest_id,))

            # Delete only unprotected rules from old digest
            deletion_result = rule_service.delete_rules_by_digest(old_digest_id)
            deleted_count = deletion_result["deleted"]

            logger.info(f"Re-digest: Deleted {deleted_count} unprotected rules, preserved {protected_count} protected rules")
        else:
            # First digest
            new_version = 1
            deleted_count = 0
            protected_count = 0
            logger.info(f"First digest for source {source_id}")

        # Create new digest version
        cursor.execute("""
            INSERT INTO legislation_digests (
                legislation_source_id, digest_type, version, active, created_at
            ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (source_id, 'universal', new_version, 1))

        new_digest_id = cursor.lastrowid
        db.conn.commit()

        logger.info(f"Created new digest version {new_version} with id {new_digest_id}")

        # Parse legislation into rules using LLM
        parser = DocumentParserService()
        parsed_rules = await parser.parse_legislation_to_rules(
            legislation_text=legislation_source.full_text,
            state_code=legislation_source.state_code,
            statute_number=legislation_source.statute_number
        )

        # Create new rules linked to new digest
        created_rules = []
        for rule_data in parsed_rules:
            rule_create = RuleCreate(
                state_code=legislation_source.state_code,
                legislation_source_id=source_id,
                legislation_digest_id=new_digest_id,  # Link to new digest
                rule_text=rule_data["rule_text"],
                applies_to_page_types=rule_data.get("applies_to_page_types"),
                active=True,
                approved=False,  # Requires manual review
                is_manually_modified=False,
                status='active'
            )

            rule = rule_service.create_rule(rule_create)
            created_rules.append(rule)
            logger.info(f"Created rule {rule.id} linked to digest {new_digest_id}")

        return {
            "message": f"Successfully digested legislation into {len(created_rules)} new rules",
            "legislation_source_id": source_id,
            "statute_number": legislation_source.statute_number,
            "digest_id": new_digest_id,
            "digest_version": new_version,
            "deleted_count": deleted_count,
            "protected_count": protected_count,
            "created_count": len(created_rules),
            "rules": created_rules,
            "requires_review": True
        }

    except ValueError as e:
        logger.error(f"ValueError in digest: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Exception in digest: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to digest legislation: {str(e)}")
