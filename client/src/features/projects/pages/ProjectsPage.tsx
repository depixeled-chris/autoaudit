import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppSelector } from '@store/hooks';
import { useGetProjectsQuery, useCaptureProjectScreenshotMutation } from '../projectsApi';
import { Card, CardHeader, CardTitle, CardContent } from '@components/ui/Card';
import { Button } from '@components/ui/Button';
import { Plus, Folder, Camera, ExternalLink } from 'lucide-react';
import { CreateProjectModal } from '../components/CreateProjectModal';
import styles from './ProjectsPage.module.scss';

export function ProjectsPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAppSelector((state) => state.auth);
  const { data: projectsList, isLoading, error } = useGetProjectsQuery(undefined, {
    skip: !isAuthenticated, // Only fetch if authenticated
  });
  const [captureScreenshot, { isLoading: isCapturing }] = useCaptureProjectScreenshotMutation();
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleProjectClick = (projectId: number) => {
    navigate(`/projects/${projectId}`);
  };

  const handleCaptureScreenshot = async (projectId: number, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent card click
    try {
      await captureScreenshot(projectId).unwrap();
    } catch (err) {
      console.error('Failed to capture screenshot:', err);
    }
  };

  // Show placeholder while not authenticated
  if (!isAuthenticated) {
    return null;
  }

  if (isLoading) {
    return (
      <div className={styles.loading}>
        <p>Loading projects...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.error}>
        <p>Failed to load projects: {error instanceof Error ? error.message : 'Unknown error'}</p>
      </div>
    );
  }

  return (
    <div className={styles.projects}>
      <div className={styles.header}>
        <div>
          <h1>Projects</h1>
          <p>Manage your compliance monitoring projects</p>
        </div>
        <Button variant="primary" onClick={() => setIsModalOpen(true)}>
          <Plus size={20} />
          New Project
        </Button>
      </div>

      {!projectsList || projectsList.length === 0 ? (
        <Card>
          <CardContent>
            <div className={styles.empty}>
              <Folder size={48} />
              <h3>No projects yet</h3>
              <p>Create your first project to start monitoring compliance</p>
              <Button variant="primary" onClick={() => setIsModalOpen(true)}>
                <Plus size={20} />
                Create Project
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className={styles.grid}>
          {projectsList.map((project) => (
            <Card key={project.id} hover>
              {project.screenshot_path ? (
                <div
                  className={styles.screenshot}
                  onClick={() => handleProjectClick(project.id)}
                  style={{ cursor: 'pointer' }}
                >
                  <img
                    src={`${import.meta.env.VITE_API_URL}/${project.screenshot_path}`}
                    alt={`${project.name} screenshot`}
                    loading="lazy"
                  />
                </div>
              ) : (
                <div
                  className={styles.screenshotPlaceholder}
                  onClick={() => handleProjectClick(project.id)}
                  style={{ cursor: 'pointer' }}
                >
                  <Folder size={48} />
                </div>
              )}
              <CardHeader>
                <CardTitle
                  onClick={() => handleProjectClick(project.id)}
                  style={{ cursor: 'pointer' }}
                >
                  {project.name}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className={styles.projectInfo}>
                  {project.base_url && (
                    <p className={styles.baseUrl}>
                      <a
                        href={project.base_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <ExternalLink size={14} />
                        {project.base_url}
                      </a>
                    </p>
                  )}
                  <p className={styles.description}>{project.description}</p>
                  <div className={styles.meta}>
                    <span className={styles.badge}>{project.state_code}</span>
                    <span className={styles.date}>
                      Created {new Date(project.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  {project.base_url && (
                    <Button
                      variant="secondary"
                      onClick={(e) => handleCaptureScreenshot(project.id, e)}
                      disabled={isCapturing}
                      style={{ marginTop: '0.5rem', width: '100%' }}
                    >
                      <Camera size={16} />
                      {project.screenshot_path ? 'Update Screenshot' : 'Capture Screenshot'}
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <CreateProjectModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </div>
  );
}
