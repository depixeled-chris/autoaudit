"""Centralized LLM operation type constants and metadata.

All LLM operations must use these constants for logging and model configuration.
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class LLMOperationType:
    """Metadata for an LLM operation type."""
    code: str  # ALL_CAPS_SNAKE_CASE identifier
    description: str
    default_model: str = 'gpt-4o-mini'


# LLM Operation Type Constants
PARSE_LEGISLATION = 'PARSE_LEGISLATION'
GENERATE_RULES = 'GENERATE_RULES'
DETECT_COLLISIONS = 'DETECT_COLLISIONS'
GENERATE_PREAMBLE = 'GENERATE_PREAMBLE'
COMPLIANCE_CHECK = 'COMPLIANCE_CHECK'


# Operation type metadata registry
OPERATION_TYPES: Dict[str, LLMOperationType] = {
    PARSE_LEGISLATION: LLMOperationType(
        code=PARSE_LEGISLATION,
        description='Parse uploaded legislation documents into structured data',
        default_model='gpt-4o-mini'
    ),
    GENERATE_RULES: LLMOperationType(
        code=GENERATE_RULES,
        description='Generate atomic compliance rules from legislation',
        default_model='gpt-4o-mini'
    ),
    DETECT_COLLISIONS: LLMOperationType(
        code=DETECT_COLLISIONS,
        description='Detect semantic collisions between rules',
        default_model='gpt-4o-mini'
    ),
    GENERATE_PREAMBLE: LLMOperationType(
        code=GENERATE_PREAMBLE,
        description='Generate page-specific preambles',
        default_model='gpt-4o-mini'
    ),
    COMPLIANCE_CHECK: LLMOperationType(
        code=COMPLIANCE_CHECK,
        description='Check URL compliance against rules',
        default_model='gpt-4o-mini'
    ),
}


def get_all_operation_types() -> List[Dict[str, str]]:
    """Get all operation types with metadata for API responses."""
    return [
        {
            'code': op.code,
            'description': op.description,
            'default_model': op.default_model,
        }
        for op in OPERATION_TYPES.values()
    ]


def get_operation_type(code: str) -> LLMOperationType:
    """Get operation type metadata by code."""
    if code not in OPERATION_TYPES:
        raise ValueError(f"Unknown LLM operation type: {code}")
    return OPERATION_TYPES[code]


def validate_operation_type(code: str) -> bool:
    """Validate that an operation type code exists."""
    return code in OPERATION_TYPES
