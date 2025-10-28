"""API routes for LLM logging and model configuration."""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel

from core.database import ComplianceDatabase
from core.llm_operations import get_all_operation_types, validate_operation_type
from api.dependencies import get_db, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/llm", tags=["llm"])


# Schemas
class LLMLogResponse(BaseModel):
    id: int
    api_endpoint: str
    operation_type: str
    user_id: Optional[int]
    model: str
    provider: str
    input_text: str
    output_text: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost_usd: Optional[float]
    output_cost_usd: Optional[float]
    total_cost_usd: Optional[float]
    duration_ms: Optional[int]
    status: str
    error_message: Optional[str]
    request_id: Optional[str]
    related_entity_type: Optional[str]
    related_entity_id: Optional[int]
    created_at: datetime


class LLMLogsListResponse(BaseModel):
    logs: List[LLMLogResponse]
    total: int
    total_cost_usd: float


class LLMStatsResponse(BaseModel):
    total_calls: int
    total_tokens: int
    total_cost_usd: float
    avg_duration_ms: int
    by_operation: List[Dict]
    by_model: List[Dict]
    by_status: List[Dict]


class ModelConfigResponse(BaseModel):
    id: int
    operation_type: str
    model: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime


class ModelConfigUpdate(BaseModel):
    model: str


class ModelConfigsListResponse(BaseModel):
    configs: List[ModelConfigResponse]
    total: int


# LLM Logs Endpoints
@router.get("/logs", response_model=LLMLogsListResponse)
async def list_llm_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    operation_type: Optional[str] = None,
    model: Optional[str] = None,
    status: Optional[str] = None,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """List LLM logs with optional filtering."""
    cursor = db.conn.cursor()

    where_clauses = []
    params = []

    if operation_type:
        where_clauses.append("operation_type = ?")
        params.append(operation_type)

    if model:
        where_clauses.append("model = ?")
        params.append(model)

    if status:
        where_clauses.append("status = ?")
        params.append(status)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    # Get total count
    cursor.execute(f"SELECT COUNT(*) FROM llm_logs {where_sql}", params)
    total = cursor.fetchone()[0]

    # Get total cost
    cursor.execute(
        f"SELECT COALESCE(SUM(total_cost_usd), 0) FROM llm_logs {where_sql}",
        params
    )
    total_cost = cursor.fetchone()[0]

    # Get logs
    cursor.execute(f"""
        SELECT
            id, api_endpoint, operation_type, user_id, model, provider,
            input_text, output_text, input_tokens, output_tokens, total_tokens,
            input_cost_usd, output_cost_usd, total_cost_usd, duration_ms,
            status, error_message, request_id, related_entity_type, related_entity_id,
            created_at
        FROM llm_logs
        {where_sql}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """, params + [limit, offset])

    logs = []
    for row in cursor.fetchall():
        logs.append(LLMLogResponse(
            id=row[0],
            api_endpoint=row[1],
            operation_type=row[2],
            user_id=row[3],
            model=row[4],
            provider=row[5],
            input_text=row[6],
            output_text=row[7],
            input_tokens=row[8],
            output_tokens=row[9],
            total_tokens=row[10],
            input_cost_usd=row[11],
            output_cost_usd=row[12],
            total_cost_usd=row[13],
            duration_ms=row[14],
            status=row[15],
            error_message=row[16],
            request_id=row[17],
            related_entity_type=row[18],
            related_entity_id=row[19],
            created_at=datetime.fromisoformat(row[20])
        ))

    return LLMLogsListResponse(
        logs=logs,
        total=total,
        total_cost_usd=round(total_cost, 4)
    )


@router.get("/logs/{log_id}", response_model=LLMLogResponse)
async def get_llm_log(
    log_id: int,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get a specific LLM log by ID."""
    cursor = db.conn.cursor()

    cursor.execute("""
        SELECT
            id, api_endpoint, operation_type, user_id, model, provider,
            input_text, output_text, input_tokens, output_tokens, total_tokens,
            input_cost_usd, output_cost_usd, total_cost_usd, duration_ms,
            status, error_message, request_id, related_entity_type, related_entity_id,
            created_at
        FROM llm_logs
        WHERE id = ?
    """, (log_id,))

    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="LLM log not found")

    return LLMLogResponse(
        id=row[0],
        api_endpoint=row[1],
        operation_type=row[2],
        user_id=row[3],
        model=row[4],
        provider=row[5],
        input_text=row[6],
        output_text=row[7],
        input_tokens=row[8],
        output_tokens=row[9],
        total_tokens=row[10],
        input_cost_usd=row[11],
        output_cost_usd=row[12],
        total_cost_usd=row[13],
        duration_ms=row[14],
        status=row[15],
        error_message=row[16],
        request_id=row[17],
        related_entity_type=row[18],
        related_entity_id=row[19],
        created_at=datetime.fromisoformat(row[20])
    )


@router.get("/stats", response_model=LLMStatsResponse)
async def get_llm_stats(
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get aggregate LLM usage statistics."""
    cursor = db.conn.cursor()

    # Overall stats
    cursor.execute("""
        SELECT
            COUNT(*) as total_calls,
            COALESCE(SUM(total_tokens), 0) as total_tokens,
            COALESCE(SUM(total_cost_usd), 0) as total_cost,
            COALESCE(AVG(duration_ms), 0) as avg_duration
        FROM llm_logs
    """)
    row = cursor.fetchone()
    total_calls, total_tokens, total_cost, avg_duration = row

    # By operation type
    cursor.execute("""
        SELECT
            operation_type,
            COUNT(*) as calls,
            COALESCE(SUM(total_tokens), 0) as tokens,
            COALESCE(SUM(total_cost_usd), 0) as cost
        FROM llm_logs
        GROUP BY operation_type
        ORDER BY cost DESC
    """)
    by_operation = [
        {
            "operation_type": row[0],
            "calls": row[1],
            "tokens": row[2],
            "cost_usd": round(row[3], 4)
        }
        for row in cursor.fetchall()
    ]

    # By model
    cursor.execute("""
        SELECT
            model,
            COUNT(*) as calls,
            COALESCE(SUM(total_tokens), 0) as tokens,
            COALESCE(SUM(total_cost_usd), 0) as cost
        FROM llm_logs
        GROUP BY model
        ORDER BY cost DESC
    """)
    by_model = [
        {
            "model": row[0],
            "calls": row[1],
            "tokens": row[2],
            "cost_usd": round(row[3], 4)
        }
        for row in cursor.fetchall()
    ]

    # By status
    cursor.execute("""
        SELECT
            status,
            COUNT(*) as calls
        FROM llm_logs
        GROUP BY status
    """)
    by_status = [
        {"status": row[0], "calls": row[1]}
        for row in cursor.fetchall()
    ]

    return LLMStatsResponse(
        total_calls=total_calls,
        total_tokens=total_tokens,
        total_cost_usd=round(total_cost, 4),
        avg_duration_ms=int(avg_duration),
        by_operation=by_operation,
        by_model=by_model,
        by_status=by_status
    )


# Operation Types Endpoint
@router.get("/operations", response_model=List[Dict])
async def get_operation_types(
    current_user: Dict = Depends(get_current_user)
):
    """Get list of all LLM operation types with metadata."""
    return get_all_operation_types()


# Available Models Endpoint
@router.get("/models/available", response_model=List[str])
async def get_available_models(
    current_user: Dict = Depends(get_current_user)
):
    """Get list of available OpenAI models."""
    # TODO: In the future, fetch this from OpenAI API
    # For now, return a curated list of models we support with pricing
    return [
        'gpt-4o',
        'gpt-4o-mini',
        'gpt-4-turbo',
        'gpt-3.5-turbo',
    ]


# Model Configuration Endpoints
@router.get("/models", response_model=ModelConfigsListResponse)
async def list_model_configs(
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """List all model configurations."""
    cursor = db.conn.cursor()

    cursor.execute("""
        SELECT id, operation_type, model, description, created_at, updated_at
        FROM llm_model_config
        ORDER BY operation_type
    """)

    configs = []
    for row in cursor.fetchall():
        configs.append(ModelConfigResponse(
            id=row[0],
            operation_type=row[1],
            model=row[2],
            description=row[3],
            created_at=datetime.fromisoformat(row[4]),
            updated_at=datetime.fromisoformat(row[5])
        ))

    return ModelConfigsListResponse(configs=configs, total=len(configs))


@router.patch("/models/{operation_type}", response_model=ModelConfigResponse)
async def update_model_config(
    operation_type: str,
    update_data: ModelConfigUpdate,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Update the model for a specific operation type."""
    cursor = db.conn.cursor()

    # Check if config exists
    cursor.execute(
        "SELECT id FROM llm_model_config WHERE operation_type = ?",
        (operation_type,)
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Model configuration not found")

    # Update model
    cursor.execute("""
        UPDATE llm_model_config
        SET model = ?, updated_at = CURRENT_TIMESTAMP
        WHERE operation_type = ?
    """, (update_data.model, operation_type))

    db.conn.commit()

    logger.info(f"Updated model config: {operation_type} → {update_data.model}")

    # Return updated config
    cursor.execute("""
        SELECT id, operation_type, model, description, created_at, updated_at
        FROM llm_model_config
        WHERE operation_type = ?
    """, (operation_type,))

    row = cursor.fetchone()
    return ModelConfigResponse(
        id=row[0],
        operation_type=row[1],
        model=row[2],
        description=row[3],
        created_at=datetime.fromisoformat(row[4]),
        updated_at=datetime.fromisoformat(row[5])
    )
