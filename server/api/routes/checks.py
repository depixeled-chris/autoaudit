"""Compliance check API routes."""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import List, Optional
import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.database import ComplianceDatabase
from core.config import DATABASE_PATH
from core.main_hybrid import HybridComplianceChecker
from schemas.check import CheckRequest, CheckResponse, ViolationResponse, VisualVerificationResponse

router = APIRouter()


def get_db():
    """Get database instance."""
    return ComplianceDatabase(DATABASE_PATH)


@router.post("/", response_model=CheckResponse, status_code=201)
async def run_compliance_check(check_request: CheckRequest):
    """
    Run a compliance check on a URL.

    This performs:
    1. Web scraping with Playwright
    2. Template-based content extraction
    3. GPT-4.1-nano text analysis
    4. GPT-4V visual verification (if needed)
    5. Template caching for future checks

    The check may take 30-60 seconds depending on visual verification needs.
    """
    try:
        # Initialize checker
        checker = HybridComplianceChecker(
            state_code=check_request.state_code,
            output_dir="reports"
        )

        # Run check
        result = await checker.check_url(
            url=check_request.url,
            save_formats=check_request.save_formats,
            skip_visual=check_request.skip_visual
        )

        # Save to database
        db = get_db()
        try:
            check_id = db.save_compliance_check(
                url=check_request.url,
                state_code=check_request.state_code,
                template_id=result.get('template_id'),
                overall_score=result.get('overall_compliance_score', 0),
                compliance_status=result.get('compliance_status', 'UNKNOWN'),
                summary=result.get('summary', ''),
                llm_input_path=result.get('report_paths', {}).get('llm_input'),
                report_path=result.get('report_paths', {}).get('markdown')
            )

            # Save violations
            for violation in result.get('violations', []):
                db.save_violation(
                    check_id=check_id,
                    category=violation.get('category', 'unknown'),
                    severity=violation.get('severity', 'unknown'),
                    rule_violated=violation.get('rule_violated', ''),
                    rule_key=violation.get('rule_key'),
                    confidence=violation.get('confidence'),
                    needs_visual_verification=violation.get('needs_visual_verification', False),
                    explanation=violation.get('explanation'),
                    evidence=violation.get('evidence')
                )

            # Save visual verifications
            for visual in result.get('visual_verifications', []):
                db.save_visual_verification(
                    check_id=check_id,
                    rule_key=visual.get('rule_key', ''),
                    rule_text=visual.get('rule', ''),
                    is_compliant=visual.get('is_compliant', False),
                    confidence=visual.get('confidence', 0.0),
                    verification_method=visual.get('verification_method', 'visual'),
                    visual_evidence=visual.get('visual_evidence'),
                    proximity_description=visual.get('proximity_description'),
                    screenshot_path=visual.get('screenshot_path'),
                    cached=visual.get('cached', False)
                )

            # Fetch complete check with related data
            check = db.get_compliance_check(check_id)
            violations = db.get_violations(check_id)
            visual_verifications = db.get_visual_verifications(check_id)

            return CheckResponse(
                **check,
                violations=[ViolationResponse(**v) for v in violations],
                visual_verifications=[VisualVerificationResponse(**vv) for vv in visual_verifications]
            )
        finally:
            db.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Check failed: {str(e)}")


@router.get("/", response_model=List[CheckResponse])
async def list_checks(
    url_id: Optional[int] = Query(None, description="Filter by URL ID"),
    state_code: Optional[str] = Query(None, description="Filter by state code"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results")
):
    """
    List compliance checks.

    Returns checks ordered by timestamp (newest first).
    Can be filtered by URL ID and/or state code.
    """
    db = get_db()
    try:
        checks = db.list_checks(url_id=url_id, state_code=state_code, limit=limit)
        return [CheckResponse(**c) for c in checks]
    finally:
        db.close()


@router.get("/{check_id}", response_model=CheckResponse)
async def get_check(check_id: int, include_details: bool = Query(True, description="Include violations and visual verifications")):
    """
    Get a specific compliance check by ID.

    Optionally include related violations and visual verifications.
    """
    db = get_db()
    try:
        check = db.get_compliance_check(check_id)
        if not check:
            raise HTTPException(status_code=404, detail="Check not found")

        if include_details:
            violations = db.get_violations(check_id)
            visual_verifications = db.get_visual_verifications(check_id)

            return CheckResponse(
                **check,
                violations=[ViolationResponse(**v) for v in violations],
                visual_verifications=[VisualVerificationResponse(**vv) for vv in visual_verifications]
            )
        else:
            return CheckResponse(**check)
    finally:
        db.close()


@router.get("/{check_id}/violations", response_model=List[ViolationResponse])
async def get_check_violations(check_id: int):
    """
    Get all violations for a specific check.
    """
    db = get_db()
    try:
        check = db.get_compliance_check(check_id)
        if not check:
            raise HTTPException(status_code=404, detail="Check not found")

        violations = db.get_violations(check_id)
        return [ViolationResponse(**v) for v in violations]
    finally:
        db.close()


@router.get("/{check_id}/visual-verifications", response_model=List[VisualVerificationResponse])
async def get_check_visual_verifications(check_id: int):
    """
    Get all visual verifications for a specific check.
    """
    db = get_db()
    try:
        check = db.get_compliance_check(check_id)
        if not check:
            raise HTTPException(status_code=404, detail="Check not found")

        visual_verifications = db.get_visual_verifications(check_id)
        return [VisualVerificationResponse(**vv) for vv in visual_verifications]
    finally:
        db.close()


@router.get("/url/{url}", response_model=CheckResponse)
async def get_latest_check_for_url(url: str):
    """
    Get the most recent compliance check for a specific URL.
    """
    db = get_db()
    try:
        check = db.get_latest_check(url)
        if not check:
            raise HTTPException(status_code=404, detail="No checks found for this URL")

        check_id = check['id']
        violations = db.get_violations(check_id)
        visual_verifications = db.get_visual_verifications(check_id)

        return CheckResponse(
            **check,
            violations=[ViolationResponse(**v) for v in violations],
            visual_verifications=[VisualVerificationResponse(**vv) for vv in visual_verifications]
        )
    finally:
        db.close()
