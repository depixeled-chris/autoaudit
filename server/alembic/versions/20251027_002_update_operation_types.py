"""Update operation_type values to ALL_CAPS constants

Revision ID: 20251027_002
Revises: 20251027_001
Create Date: 2025-10-27

Updates operation_type values from snake_case to ALL_CAPS_SNAKE_CASE
to match centralized constants in core/llm_operations.py
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision: str = '20251027_002'
down_revision: Union[str, None] = '20251027_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update operation types to ALL_CAPS format."""
    conn = op.get_bind()

    # Mapping from old snake_case to new ALL_CAPS
    mappings = [
        ('parse_legislation', 'PARSE_LEGISLATION'),
        ('generate_rules', 'GENERATE_RULES'),
        ('detect_collisions', 'DETECT_COLLISIONS'),
        ('generate_preamble', 'GENERATE_PREAMBLE'),
        ('compliance_check', 'COMPLIANCE_CHECK'),
    ]

    # Update llm_model_config table
    for old_type, new_type in mappings:
        conn.execute(
            text("UPDATE llm_model_config SET operation_type = :new WHERE operation_type = :old"),
            {"new": new_type, "old": old_type}
        )

    # Update llm_logs table
    for old_type, new_type in mappings:
        conn.execute(
            text("UPDATE llm_logs SET operation_type = :new WHERE operation_type = :old"),
            {"new": new_type, "old": old_type}
        )

    print("✓ Updated operation_type values to ALL_CAPS constants")


def downgrade() -> None:
    """Revert operation types to snake_case format."""
    conn = op.get_bind()

    # Mapping from ALL_CAPS back to snake_case
    mappings = [
        ('PARSE_LEGISLATION', 'parse_legislation'),
        ('GENERATE_RULES', 'generate_rules'),
        ('DETECT_COLLISIONS', 'detect_collisions'),
        ('GENERATE_PREAMBLE', 'generate_preamble'),
        ('COMPLIANCE_CHECK', 'compliance_check'),
    ]

    # Revert llm_model_config table
    for new_type, old_type in mappings:
        conn.execute(
            text("UPDATE llm_model_config SET operation_type = :old WHERE operation_type = :new"),
            {"old": old_type, "new": new_type}
        )

    # Revert llm_logs table
    for new_type, old_type in mappings:
        conn.execute(
            text("UPDATE llm_logs SET operation_type = :old WHERE operation_type = :new"),
            {"old": old_type, "new": new_type}
        )

    print("✓ Reverted operation_type values to snake_case")
