"""API routes for states and legislation management."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Optional, Dict
from datetime import date

from core.database import ComplianceDatabase
from api.dependencies import get_db, get_current_user
from services.state_service import StateService
from services.document_parser_service import DocumentParserService
from schemas.state import (
    StateCreate, StateUpdate, StateResponse, StatesListResponse,
    LegislationSourceCreate, LegislationSourceUpdate, LegislationSourceResponse,
    LegislationSourcesListResponse,
    LegislationDigestCreate, LegislationDigestUpdate, LegislationDigestResponse,
    LegislationDigestsListResponse
)

router = APIRouter(prefix="/states", tags=["states"])


# States
@router.post("", response_model=StateResponse, status_code=status.HTTP_201_CREATED)
async def create_state(
    state_data: StateCreate,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Create a new state."""
    service = StateService(db)
    try:
        return service.create_state(state_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=StatesListResponse)
async def list_states(
    active_only: bool = False,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """List all states."""
    service = StateService(db)
    states = service.list_states(active_only=active_only)
    return StatesListResponse(states=states, total=len(states))


@router.get("/code/{state_code}", response_model=StateResponse)
async def get_state_by_code(
    state_code: str,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get a state by code."""
    service = StateService(db)
    state = service.get_state_by_code(state_code)
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    return state



# Legislation Sources
@router.post("/legislation/upload", response_model=Dict, status_code=status.HTTP_201_CREATED)
async def upload_legislation_document(
    file: UploadFile = File(...),
    state_code: str = Form(...),
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Upload and digest a legislation document (PDF, Markdown, or Plain Text).
    The document will be digested using AI and legislation sources with digests will be created.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Upload started for file: {file.filename}, state: {state_code}")

    # Validate file type
    allowed_types = ["application/pdf", "text/markdown", "text/plain"]
    allowed_extensions = [".pdf", ".md", ".txt"]

    file_extension = file.filename.lower().split(".")[-1] if "." in file.filename else ""
    logger.info(f"File extension: {file_extension}, content_type: {file.content_type}")

    if file.content_type not in allowed_types and f".{file_extension}" not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: PDF, Markdown (.md), Plain Text (.txt)"
        )

    # Read file content
    try:
        logger.info("Reading file content...")
        file_content = await file.read()
        logger.info(f"File read successfully, size: {len(file_content)} bytes")
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")

        if len(file_content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")

    except Exception as e:
        logger.error(f"Failed to read file: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    # Digest document with AI
    try:
        logger.info("Starting document parsing with AI...")
        parser = DocumentParserService()
        logger.info("DocumentParserService instantiated")
        parsed_data = await parser.parse_document(
            file_content=file_content,
            filename=file.filename,
            state_code=state_code,
            mime_type=file.content_type or ""
        )
        logger.info("Document parsed successfully")
    except ValueError as e:
        logger.error(f"ValueError during parsing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Exception during parsing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to digest document: {str(e)}")

    # Create legislation source
    try:
        service = StateService(db)

        # Create the legislation source
        source_create = LegislationSourceCreate(
            state_code=state_code,
            statute_number=parsed_data["statute_number"],
            title=parsed_data["title"],
            full_text=parsed_data["full_text"],
            source_url=parsed_data.get("source_url"),
            effective_date=date.fromisoformat(parsed_data["effective_date"]) if parsed_data.get("effective_date") else None,
            sunset_date=date.fromisoformat(parsed_data["sunset_date"]) if parsed_data.get("sunset_date") else None,
            applies_to_page_types=parsed_data.get("applies_to_page_types")
        )

        legislation_source = service.create_legislation_source(source_create)
        logger.info(f"Created legislation source ID: {legislation_source.id}")

        # Create single digest with combined requirements
        digest = None
        if parsed_data.get("digests"):
            logger.info(f"Parser returned {len(parsed_data['digests'])} digest sections")

            # Combine all interpreted requirements into one digest
            all_requirements = []
            for digest_data in parsed_data["digests"]:
                requirements = digest_data.get("interpreted_requirements", "")
                if requirements:
                    all_requirements.append(requirements)

            combined_requirements = "\n\n".join(all_requirements)

            logger.info("Creating single digest with combined requirements")
            digest_create = LegislationDigestCreate(
                legislation_source_id=legislation_source.id,
                interpreted_requirements=combined_requirements,
                approved=False,  # Requires manual review
                created_by=current_user.get("id")
            )

            digest = service.create_legislation_digest(digest_create)
            logger.info(f"Created digest successfully with ID: {digest.id}")

            # Generate rules from the digest using LLM
            from services.rule_service import RuleService
            from schemas.rule import RuleCreate

            rule_service = RuleService(db)
            parser = DocumentParserService()

            logger.info(f"Generating rules from digest {digest.id}")
            parsed_rules = await parser.parse_legislation_to_rules(
                legislation_text=legislation_source.full_text,
                state_code=legislation_source.state_code,
                statute_number=legislation_source.statute_number
            )

            # Create rules linked to the digest
            created_rules = []
            for rule_data in parsed_rules:
                rule_create = RuleCreate(
                    state_code=legislation_source.state_code,
                    legislation_source_id=legislation_source.id,
                    legislation_digest_id=digest.id,
                    rule_text=rule_data["rule_text"],
                    applies_to_page_types=rule_data.get("applies_to_page_types"),
                    active=True,
                    approved=False,
                    is_manually_modified=False,
                    status='active'
                )
                rule = rule_service.create_rule(rule_create)
                created_rules.append(rule)
                logger.info(f"Created rule {rule.id} linked to digest {digest.id}")

            logger.info(f"Generated {len(created_rules)} rules from digest {digest.id}")

        return {
            "message": "Document uploaded and digested successfully",
            "legislation_source": legislation_source,
            "digest": digest,
            "rules_created": len(created_rules) if digest else 0,
            "requires_review": True
        }

    except ValueError as e:
        logger.error(f"ValueError in upload: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Exception in upload: {str(e)}", exc_info=True)
        error_msg = str(e)

        # Provide user-friendly error for duplicate legislation
        if "UNIQUE constraint failed" in error_msg and "legislation_sources" in error_msg:
            raise HTTPException(
                status_code=400,
                detail=f"Legislation source '{parsed_data['statute_number']}' already exists for state {state_code}. Please delete the existing source first or use manual entry to update it."
            )

        raise HTTPException(status_code=500, detail=f"Failed to create legislation: {error_msg}")


@router.post("/legislation", response_model=LegislationSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_legislation_source(
    source_data: LegislationSourceCreate,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Create a new legislation source."""
    service = StateService(db)
    try:
        return service.create_legislation_source(source_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/legislation", response_model=LegislationSourcesListResponse)
async def list_legislation_sources(
    state_code: Optional[str] = None,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """List legislation sources, optionally filtered by state."""
    service = StateService(db)
    sources = service.list_legislation_sources(state_code=state_code)
    return LegislationSourcesListResponse(sources=sources, total=len(sources))



@router.get("/legislation/{source_id}", response_model=LegislationSourceResponse)
async def get_legislation_source(
    source_id: int,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get a legislation source by ID."""
    service = StateService(db)
    source = service.get_legislation_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Legislation source not found")
    return source



@router.patch("/legislation/{source_id}", response_model=LegislationSourceResponse)
async def update_legislation_source(
    source_id: int,
    source_data: LegislationSourceUpdate,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Update a legislation source."""
    service = StateService(db)
    try:
        return service.update_legislation_source(source_id, source_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/legislation/{source_id}", status_code=status.HTTP_200_OK)
async def delete_legislation_source(
    source_id: int,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Delete a legislation source and all associated data.

    This will cascade delete:
    - All legislation digests for this source
    - All compliance rules generated from this source

    This action cannot be undone.
    """
    service = StateService(db)
    try:
        deleted_info = service.delete_legislation_source(source_id)
        return {
            "message": "Legislation source deleted successfully",
            **deleted_info
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete legislation source: {str(e)}")


# Legislation Digests

@router.post("/legislation/{source_id}/digests", response_model=LegislationDigestResponse, status_code=status.HTTP_201_CREATED)
async def create_legislation_digest(
    source_id: int,
    digest_data: LegislationDigestCreate,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Create a new legislation digest."""
    service = StateService(db)

    # Ensure source_id matches
    if digest_data.legislation_source_id != source_id:
        raise HTTPException(
            status_code=400,
            detail="legislation_source_id in body must match source_id in path"
        )

    try:
        return service.create_legislation_digest(digest_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/legislation/{source_id}/digests", response_model=LegislationDigestsListResponse)
async def list_legislation_digests(
    source_id: int,
    approved_only: bool = False,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """List legislation digests for a source."""
    service = StateService(db)
    digests = service.list_legislation_digests(
        legislation_source_id=source_id,
        approved_only=approved_only
    )
    return LegislationDigestsListResponse(digests=digests, total=len(digests))



@router.get("/digests/{digest_id}", response_model=LegislationDigestResponse)
async def get_legislation_digest(
    digest_id: int,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get a legislation digest by ID."""
    service = StateService(db)
    digest = service.get_legislation_digest(digest_id)
    if not digest:
        raise HTTPException(status_code=404, detail="Legislation digest not found")
    return digest



@router.patch("/digests/{digest_id}", response_model=LegislationDigestResponse)
async def update_legislation_digest(
    digest_id: int,
    digest_data: LegislationDigestUpdate,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Update a legislation digest."""
    service = StateService(db)
    try:
        return service.update_legislation_digest(digest_id, digest_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{state_id}", response_model=StateResponse)
async def get_state(
    state_id: int,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get a state by ID."""
    service = StateService(db)
    state = service.get_state(state_id)
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    return state



@router.patch("/{state_id}", response_model=StateResponse)
async def update_state(
    state_id: int,
    state_data: StateUpdate,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Update a state."""
    service = StateService(db)
    try:
        return service.update_state(state_id, state_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Legislation Sources







