"""URL management API routes."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.database import ComplianceDatabase
from core.config import DATABASE_PATH
from schemas.url import URLCreate, URLResponse, URLUpdate

router = APIRouter()


def get_db():
    """Get database instance."""
    return ComplianceDatabase(DATABASE_PATH)


@router.post("/", response_model=URLResponse, status_code=201)
async def add_url(url_data: URLCreate):
    """
    Add a new URL to monitor.

    URLs represent specific pages to check for compliance.
    """
    db = get_db()
    try:
        url_id = db.add_url(
            url=url_data.url,
            project_id=url_data.project_id,
            url_type=url_data.url_type,
            template_id=url_data.template_id,
            platform=url_data.platform,
            check_frequency_hours=url_data.check_frequency_hours
        )

        # Fetch created URL
        created = db.get_url(url_id=url_id)
        if not created:
            raise HTTPException(status_code=500, detail="Failed to retrieve created URL")

        return URLResponse(**created)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.get("/", response_model=List[URLResponse])
async def list_urls(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    active_only: bool = Query(True, description="Only return active URLs")
):
    """
    List URLs.

    Optionally filter by project and/or active status.
    """
    db = get_db()
    try:
        urls = db.list_urls(project_id=project_id, active_only=active_only)
        return [URLResponse(**u) for u in urls]
    finally:
        db.close()


@router.get("/{url_id}", response_model=URLResponse)
async def get_url(url_id: int):
    """
    Get a specific URL by ID.
    """
    db = get_db()
    try:
        url = db.get_url(url_id=url_id)
        if not url:
            raise HTTPException(status_code=404, detail="URL not found")
        return URLResponse(**url)
    finally:
        db.close()


@router.patch("/{url_id}", response_model=URLResponse)
async def update_url(url_id: int, url_update: URLUpdate):
    """
    Update a URL's settings.

    Can update active status, check frequency, and template ID.
    """
    db = get_db()
    try:
        # Check if URL exists
        url = db.get_url(url_id=url_id)
        if not url:
            raise HTTPException(status_code=404, detail="URL not found")

        # Update fields
        cursor = db.conn.cursor()
        updates = []
        params = []

        if url_update.active is not None:
            updates.append("active = ?")
            params.append(url_update.active)

        if url_update.check_frequency_hours is not None:
            updates.append("check_frequency_hours = ?")
            params.append(url_update.check_frequency_hours)

        if url_update.template_id is not None:
            updates.append("template_id = ?")
            params.append(url_update.template_id)

        if updates:
            params.append(url_id)
            query = f"UPDATE urls SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            db.conn.commit()

        # Fetch updated URL
        updated = db.get_url(url_id=url_id)
        return URLResponse(**updated)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.delete("/{url_id}", status_code=204)
async def delete_url(url_id: int):
    """
    Delete a URL.

    Note: Marks as inactive rather than deleting to preserve historical data.
    """
    db = get_db()
    try:
        url = db.get_url(url_id=url_id)
        if not url:
            raise HTTPException(status_code=404, detail="URL not found")

        # Mark as inactive instead of deleting
        cursor = db.conn.cursor()
        cursor.execute("UPDATE urls SET active = 0 WHERE id = ?", (url_id,))
        db.conn.commit()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()
