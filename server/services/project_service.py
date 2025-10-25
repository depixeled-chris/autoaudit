"""Project service for business logic."""

from typing import List, Optional, Dict
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.base_service import BaseService
from schemas.project import ProjectCreate, ProjectResponse, ProjectSummary
from core.database import ComplianceDatabase


class ProjectService(BaseService):
    """Service for project-related business logic."""

    def create_project(self, project_data: ProjectCreate) -> ProjectResponse:
        """
        Create a new project.

        Args:
            project_data: Project creation data

        Returns:
            Created project

        Raises:
            ValueError: If project creation fails
        """
        try:
            project_id = self.db.create_project(
                name=project_data.name,
                state_code=project_data.state_code,
                description=project_data.description,
                base_url=project_data.base_url
            )

            created = self.db.get_project(project_id=project_id)
            if not created:
                raise ValueError("Failed to retrieve created project")

            return ProjectResponse(**created)
        except Exception as e:
            raise ValueError(f"Failed to create project: {str(e)}")

    def get_project(self, project_id: int) -> Optional[ProjectResponse]:
        """
        Get a project by ID.

        Args:
            project_id: Project ID

        Returns:
            Project if found, None otherwise
        """
        project = self.db.get_project(project_id=project_id)
        if not project:
            return None
        return ProjectResponse(**project)

    def list_projects(self) -> List[ProjectResponse]:
        """
        List all projects.

        Returns:
            List of all projects
        """
        projects = self.db.list_projects()
        return [ProjectResponse(**p) for p in projects]

    def get_project_summary(self, project_id: int) -> Optional[ProjectSummary]:
        """
        Get project summary statistics.

        Args:
            project_id: Project ID

        Returns:
            Project summary if project exists, None otherwise
        """
        project = self.db.get_project(project_id=project_id)
        if not project:
            return None

        summary = self.db.get_project_summary(project_id)
        summary["project_id"] = project_id
        summary["project_name"] = project["name"]

        return ProjectSummary(**summary)

    def can_delete_project(self, project_id: int) -> bool:
        """
        Check if a project can be deleted.

        Business rule: Projects with active URLs should not be deleted.

        Args:
            project_id: Project ID

        Returns:
            True if project can be deleted, False otherwise
        """
        urls = self.db.list_urls(project_id=project_id, active_only=True)
        return len(urls) == 0

    def delete_project(self, project_id: int) -> bool:
        """
        Delete a project.

        Args:
            project_id: Project ID

        Returns:
            True if deleted, False otherwise

        Raises:
            ValueError: If project cannot be deleted
        """
        if not self.can_delete_project(project_id):
            raise ValueError("Cannot delete project with active URLs")

        # Note: Actual deletion not implemented to preserve data integrity
        # In production, implement soft delete or cascading
        raise NotImplementedError("Project deletion not implemented. Data preserved for audit trail.")
