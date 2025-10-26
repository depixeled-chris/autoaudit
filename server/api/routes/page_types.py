"""Page types API endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from core.database import ComplianceDatabase
from schemas.page_type import PageTypeCreate, PageTypeUpdate, PageTypeResponse
from api.dependencies import get_current_user, get_db

router = APIRouter(prefix="/api/page-types", tags=["page-types"])


@router.get("", response_model=List[PageTypeResponse])
async def get_page_types(
    active_only: bool = False,
    db: ComplianceDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all page types."""
    cursor = db.conn.cursor()

    if active_only:
        cursor.execute("""
            SELECT id, code, name, description, active, preamble, extraction_template,
                   requires_llm_visual_confirmation, requires_human_confirmation,
                   created_at, updated_at
            FROM page_types
            WHERE active = 1
            ORDER BY name
        """)
    else:
        cursor.execute("""
            SELECT id, code, name, description, active, preamble, extraction_template,
                   requires_llm_visual_confirmation, requires_human_confirmation,
                   created_at, updated_at
            FROM page_types
            ORDER BY name
        """)

    page_types = [dict(row) for row in cursor.fetchall()]
    return page_types


@router.get("/{page_type_id}", response_model=PageTypeResponse)
async def get_page_type(
    page_type_id: int,
    db: ComplianceDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific page type."""
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT id, code, name, description, active, preamble, extraction_template,
               requires_llm_visual_confirmation, requires_human_confirmation,
               created_at, updated_at
        FROM page_types
        WHERE id = ?
    """, (page_type_id,))

    page_type = cursor.fetchone()
    if not page_type:
        raise HTTPException(status_code=404, detail="Page type not found")

    return dict(page_type)


@router.post("", response_model=PageTypeResponse, status_code=201)
async def create_page_type(
    page_type: PageTypeCreate,
    db: ComplianceDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new page type."""
    cursor = db.conn.cursor()

    # Check if code already exists
    cursor.execute("SELECT id FROM page_types WHERE code = ?", (page_type.code,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Page type code already exists")

    cursor.execute("""
        INSERT INTO page_types (code, name, description)
        VALUES (?, ?, ?)
    """, (page_type.code, page_type.name, page_type.description))

    db.conn.commit()
    page_type_id = cursor.lastrowid

    return await get_page_type(page_type_id, db, current_user)


@router.patch("/{page_type_id}", response_model=PageTypeResponse)
async def update_page_type(
    page_type_id: int,
    page_type: PageTypeUpdate,
    db: ComplianceDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a page type."""
    cursor = db.conn.cursor()

    # Check if page type exists
    cursor.execute("SELECT id FROM page_types WHERE id = ?", (page_type_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Page type not found")

    # Build update query dynamically
    updates = []
    params = []

    if page_type.name is not None:
        updates.append("name = ?")
        params.append(page_type.name)

    if page_type.description is not None:
        updates.append("description = ?")
        params.append(page_type.description)

    if page_type.active is not None:
        updates.append("active = ?")
        params.append(page_type.active)

    if page_type.preamble is not None:
        updates.append("preamble = ?")
        params.append(page_type.preamble)

    if page_type.extraction_template is not None:
        updates.append("extraction_template = ?")
        params.append(page_type.extraction_template)

    if page_type.requires_llm_visual_confirmation is not None:
        updates.append("requires_llm_visual_confirmation = ?")
        params.append(page_type.requires_llm_visual_confirmation)

    if page_type.requires_human_confirmation is not None:
        updates.append("requires_human_confirmation = ?")
        params.append(page_type.requires_human_confirmation)

    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(page_type_id)

        query = f"UPDATE page_types SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        db.conn.commit()

    return await get_page_type(page_type_id, db, current_user)


@router.delete("/{page_type_id}", status_code=204)
async def delete_page_type(
    page_type_id: int,
    db: ComplianceDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a page type."""
    cursor = db.conn.cursor()

    # Check if page type exists
    cursor.execute("SELECT id FROM page_types WHERE id = ?", (page_type_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Page type not found")

    # Check if page type is in use
    cursor.execute("SELECT COUNT(*) as count FROM urls WHERE url_type = (SELECT code FROM page_types WHERE id = ?)", (page_type_id,))
    result = cursor.fetchone()
    if result and result['count'] > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete page type: {result['count']} URLs are using this type"
        )

    cursor.execute("DELETE FROM page_types WHERE id = ?", (page_type_id,))
    db.conn.commit()
