"""Base service class with common functionality."""

from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import ComplianceDatabase


class BaseService:
    """Base service providing database access."""

    def __init__(self, db: ComplianceDatabase):
        """
        Initialize service with database connection.

        Args:
            db: Database instance
        """
        self.db = db

    def close(self):
        """Close database connection."""
        if self.db:
            self.db.close()
