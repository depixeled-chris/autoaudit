"""
LLM Client wrapper with automatic logging for cost tracking and audit.

This module provides a wrapper around OpenAI's API that automatically logs
all LLM calls to the database for cost tracking, performance monitoring,
and audit purposes.
"""

import time
import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from openai import AsyncOpenAI

from core.database import ComplianceDatabase

logger = logging.getLogger(__name__)

# OpenAI API Pricing (2025) - Per million tokens
# Source: https://openai.com/api/pricing/
PRICING = {
    'gpt-4o': {
        'input': 3.00,      # $3 per 1M input tokens
        'output': 10.00,    # $10 per 1M output tokens
    },
    'gpt-4o-mini': {
        'input': 0.15,      # $0.15 per 1M input tokens
        'output': 0.60,     # $0.60 per 1M output tokens
    },
    'gpt-4-turbo': {
        'input': 10.00,     # $10 per 1M input tokens
        'output': 30.00,    # $30 per 1M output tokens
    },
    'gpt-4-turbo-preview': {  # Alias
        'input': 10.00,
        'output': 30.00,
    },
    'gpt-3.5-turbo': {
        'input': 0.50,      # $0.50 per 1M input tokens
        'output': 1.50,     # $1.50 per 1M output tokens
    },
    # Default fallback for unknown models
    'default': {
        'input': 10.00,
        'output': 30.00,
    }
}


class LLMClient:
    """
    OpenAI client wrapper with automatic logging.

    This client wraps OpenAI API calls and automatically logs:
    - Input/output text
    - Token usage and costs
    - Performance metrics
    - Error details

    Example:
        ```python
        llm = LLMClient(db)
        result = await llm.chat_completion(
            messages=[{"role": "user", "content": "Hello!"}],
            model='gpt-4o-mini',
            operation_type='test',
            api_endpoint='/api/test'
        )
        print(f"Response: {result['content']}")
        print(f"Cost: ${result['cost_usd']:.4f}")
        ```
    """

    def __init__(self, db: ComplianceDatabase):
        """
        Initialize LLM client.

        Args:
            db: Database connection for logging
        """
        self.client = AsyncOpenAI()
        self.db = db

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = 'gpt-4o-mini',
        operation_type: str,
        api_endpoint: str,
        user_id: Optional[int] = None,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make an OpenAI chat completion call with automatic logging.

        Args:
            messages: List of message dicts (role + content)
            model: Model to use (default: gpt-4o-mini)
            operation_type: Operation category (e.g., 'parse_legislation', 'generate_rules')
            api_endpoint: API endpoint that invoked this call
            user_id: User who triggered the operation
            related_entity_type: Type of entity (e.g., 'legislation_source', 'digest')
            related_entity_id: ID of related entity
            **kwargs: Additional OpenAI parameters (temperature, max_tokens, etc.)

        Returns:
            Dict with:
                - content: The LLM response text
                - response: Full OpenAI response object
                - log_id: Database log ID
                - usage: Token usage details
                - cost_usd: Cost in USD

        Raises:
            Exception: If OpenAI API call fails (error is logged before re-raising)
        """
        request_id = str(uuid.uuid4())

        # Combine all messages for logging
        input_text = self._format_messages_for_log(messages)

        start_time = time.time()
        status = 'success'
        error_message = None
        output_text = ''
        usage = None
        response = None

        try:
            # Make the actual LLM call
            logger.info(f"LLM call: {operation_type} using {model} (request_id: {request_id})")

            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )

            # Extract response details
            output_text = response.choices[0].message.content or ''
            usage = response.usage

            logger.info(
                f"LLM success: {usage.total_tokens} tokens, "
                f"{int((time.time() - start_time) * 1000)}ms"
            )

        except Exception as e:
            status = 'error'
            error_message = str(e)
            logger.error(f"LLM error: {error_message} (request_id: {request_id})")
            # Will re-raise after logging

        finally:
            # Always log, even on error
            duration_ms = int((time.time() - start_time) * 1000)

            # Calculate costs
            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else 0

            costs = self._calculate_cost(model, input_tokens, output_tokens)

            # Log to database
            log_id = self._log_call(
                api_endpoint=api_endpoint,
                operation_type=operation_type,
                user_id=user_id,
                model=model,
                input_text=input_text,
                output_text=output_text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                input_cost_usd=costs['input_cost'],
                output_cost_usd=costs['output_cost'],
                total_cost_usd=costs['total_cost'],
                duration_ms=duration_ms,
                status=status,
                error_message=error_message,
                request_id=request_id,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id
            )

            if status == 'error':
                # Re-raise the exception after logging
                raise

        return {
            'content': output_text,
            'response': response,
            'log_id': log_id,
            'usage': usage,
            'cost_usd': costs['total_cost'],
            'request_id': request_id
        }

    def _format_messages_for_log(self, messages: List[Dict[str, str]]) -> str:
        """Format messages array into readable text for logging."""
        formatted = []
        for msg in messages:
            role = msg.get('role', 'unknown').upper()
            content = msg.get('content', '')
            formatted.append(f"[{role}]\n{content}")
        return "\n\n".join(formatted)

    def _calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, float]:
        """
        Calculate cost based on token usage and model pricing.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Dict with input_cost, output_cost, total_cost in USD
        """
        # Get pricing for model (use default if not found)
        pricing = PRICING.get(model, PRICING['default'])

        # Convert to cost (pricing is per million tokens)
        input_cost = (input_tokens / 1_000_000) * pricing['input']
        output_cost = (output_tokens / 1_000_000) * pricing['output']
        total_cost = input_cost + output_cost

        return {
            'input_cost': round(input_cost, 6),
            'output_cost': round(output_cost, 6),
            'total_cost': round(total_cost, 6)
        }

    def _log_call(self, **kwargs) -> int:
        """
        Insert log record into database.

        Args:
            **kwargs: All log fields

        Returns:
            Log ID
        """
        cursor = self.db.conn.cursor()

        columns = ', '.join(kwargs.keys())
        placeholders = ', '.join(['?' for _ in kwargs])
        values = tuple(kwargs.values())

        cursor.execute(f"""
            INSERT INTO llm_logs ({columns})
            VALUES ({placeholders})
        """, values)

        self.db.conn.commit()
        log_id = cursor.lastrowid

        logger.debug(f"Logged LLM call: log_id={log_id}, cost=${kwargs.get('total_cost_usd', 0):.6f}")

        return log_id

    def get_usage_stats(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        operation_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get usage statistics for LLM calls.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            operation_type: Filter by operation type

        Returns:
            Dict with aggregated stats
        """
        cursor = self.db.conn.cursor()

        where_clauses = ["status = 'success'"]
        params = []

        if start_date:
            where_clauses.append("created_at >= ?")
            params.append(start_date)

        if end_date:
            where_clauses.append("created_at <= ?")
            params.append(end_date)

        if operation_type:
            where_clauses.append("operation_type = ?")
            params.append(operation_type)

        where_sql = " AND ".join(where_clauses)

        cursor.execute(f"""
            SELECT
                COUNT(*) as call_count,
                SUM(total_tokens) as total_tokens,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens,
                SUM(total_cost_usd) as total_cost,
                AVG(duration_ms) as avg_duration_ms,
                MIN(created_at) as first_call,
                MAX(created_at) as last_call
            FROM llm_logs
            WHERE {where_sql}
        """, params)

        row = cursor.fetchone()

        return {
            'call_count': row[0] or 0,
            'total_tokens': row[1] or 0,
            'total_input_tokens': row[2] or 0,
            'total_output_tokens': row[3] or 0,
            'total_cost_usd': round(row[4] or 0, 4),
            'avg_duration_ms': int(row[5] or 0),
            'first_call': row[6],
            'last_call': row[7]
        }
