"""Reporting API routes."""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import List, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.database import ComplianceDatabase
from core.config import DATABASE_PATH

router = APIRouter()


def get_db():
    """Get database instance."""
    return ComplianceDatabase(DATABASE_PATH)


@router.get("/{check_id}/markdown")
async def get_markdown_report(check_id: int):
    """
    Download the Markdown report for a compliance check.

    Returns the generated Markdown report file.
    """
    db = get_db()
    try:
        check = db.get_compliance_check(check_id)
        if not check:
            raise HTTPException(status_code=404, detail="Check not found")

        report_path = check.get('report_path')
        if not report_path:
            raise HTTPException(status_code=404, detail="Report not available")

        report_file = Path(report_path)
        if not report_file.exists():
            raise HTTPException(status_code=404, detail="Report file not found")

        return FileResponse(
            path=str(report_file),
            media_type='text/markdown',
            filename=report_file.name
        )
    finally:
        db.close()


@router.get("/{check_id}/llm-input")
async def get_llm_input(check_id: int):
    """
    Download the LLM input file for a compliance check.

    Returns the formatted input that was sent to the LLM for analysis.
    Useful for debugging and understanding what data the LLM saw.
    """
    db = get_db()
    try:
        check = db.get_compliance_check(check_id)
        if not check:
            raise HTTPException(status_code=404, detail="Check not found")

        llm_input_path = check.get('llm_input_path')
        if not llm_input_path:
            raise HTTPException(status_code=404, detail="LLM input not available")

        input_file = Path(llm_input_path)
        if not input_file.exists():
            raise HTTPException(status_code=404, detail="LLM input file not found")

        return FileResponse(
            path=str(input_file),
            media_type='text/markdown',
            filename=input_file.name
        )
    finally:
        db.close()


@router.get("/screenshots/{screenshot_filename}")
async def get_screenshot(screenshot_filename: str):
    """
    Download a screenshot from visual verification.

    Screenshots are stored in the screenshots/ directory.
    """
    screenshot_path = Path("screenshots") / screenshot_filename

    if not screenshot_path.exists():
        raise HTTPException(status_code=404, detail="Screenshot not found")

    # Security: prevent path traversal
    if not str(screenshot_path.resolve()).startswith(str(Path("screenshots").resolve())):
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(
        path=str(screenshot_path),
        media_type='image/png',
        filename=screenshot_filename
    )
