"""Template management API routes."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.database import ComplianceDatabase
from core.config import DATABASE_PATH
from schemas.template import TemplateResponse, TemplateRuleResponse, TemplateRuleUpdate

router = APIRouter()


def get_db():
    """Get database instance."""
    return ComplianceDatabase(DATABASE_PATH)


@router.get("/", response_model=List[TemplateResponse])
async def list_templates():
    """
    List all templates.

    Returns all known templates with their cached compliance rules.
    """
    db = get_db()
    try:
        cursor = db.conn.cursor()
        cursor.execute("SELECT * FROM templates ORDER BY template_id")
        templates = [dict(row) for row in cursor.fetchall()]

        result = []
        for template in templates:
            rules = db.get_template_rules(template['template_id'])
            template['rules'] = [TemplateRuleResponse(**r) for r in rules]
            result.append(TemplateResponse(**template))

        return result
    finally:
        db.close()


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: str):
    """
    Get a specific template by ID.

    Returns template details including all cached compliance rules.
    """
    db = get_db()
    try:
        template = db.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        rules = db.get_template_rules(template_id)
        template['rules'] = [TemplateRuleResponse(**r) for r in rules]

        return TemplateResponse(**template)
    finally:
        db.close()


@router.get("/{template_id}/rules", response_model=List[TemplateRuleResponse])
async def get_template_rules(template_id: str):
    """
    Get all cached rules for a template.

    Rules are compliance decisions that have been verified and cached
    to avoid expensive re-verification on similar pages.
    """
    db = get_db()
    try:
        template = db.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        rules = db.get_template_rules(template_id)
        return [TemplateRuleResponse(**r) for r in rules]
    finally:
        db.close()


@router.get("/{template_id}/rules/{rule_key}", response_model=TemplateRuleResponse)
async def get_template_rule(template_id: str, rule_key: str):
    """
    Get a specific cached rule for a template.
    """
    db = get_db()
    try:
        rule = db.get_template_rule(template_id, rule_key)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")

        return TemplateRuleResponse(**rule)
    finally:
        db.close()


@router.put("/{template_id}/rules/{rule_key}", response_model=TemplateRuleResponse)
async def update_template_rule(template_id: str, rule_key: str, rule_update: TemplateRuleUpdate):
    """
    Update or create a cached rule for a template.

    This is typically done automatically during compliance checks,
    but can be manually updated for overrides or corrections.
    """
    db = get_db()
    try:
        # Ensure template exists
        template = db.get_template(template_id)
        if not template:
            # Create template if it doesn't exist
            db.save_template(template_id, "custom")

        # Save rule
        db.save_template_rule(
            template_id=template_id,
            rule_key=rule_key,
            status=rule_update.status,
            confidence=rule_update.confidence,
            verification_method=rule_update.verification_method,
            notes=rule_update.notes
        )

        # Fetch updated rule
        rule = db.get_template_rule(template_id, rule_key)
        return TemplateRuleResponse(**rule)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.delete("/{template_id}/rules/{rule_key}", status_code=204)
async def delete_template_rule(template_id: str, rule_key: str):
    """
    Delete a cached rule.

    This will force re-verification on the next check.
    """
    db = get_db()
    try:
        rule = db.get_template_rule(template_id, rule_key)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")

        cursor = db.conn.cursor()
        cursor.execute(
            "DELETE FROM template_rules WHERE template_id = ? AND rule_key = ?",
            (template_id, rule_key)
        )
        db.conn.commit()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()
