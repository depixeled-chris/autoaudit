import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Calendar, MapPin, ExternalLink, Camera, Plus, Trash2 } from 'lucide-react';
import { useGetProjectQuery, useGetProjectSummaryQuery, useCaptureProjectScreenshotMutation, useDeleteProjectMutation } from '../projectsApi';
import { Button } from '@components/ui/Button';
import { Card } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { ConfirmModal } from '@components/ui/ConfirmModal';
import { URLList } from '@features/urls/components/URLList';
import { AddURLModal } from '@features/urls/components/AddURLModal';
import styles from './ProjectDetailPage.module.scss';

export const ProjectDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const projectId = parseInt(id || '0', 10);

  const { data: project, isLoading, error } = useGetProjectQuery(projectId);
  const { data: summary } = useGetProjectSummaryQuery(projectId);
  const [captureScreenshot, { isLoading: isCapturing }] = useCaptureProjectScreenshotMutation();
  const [deleteProject, { isLoading: isDeleting }] = useDeleteProjectMutation();
  const [isAddURLModalOpen, setIsAddURLModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  const handleCaptureScreenshot = async () => {
    if (!project) return;
    try {
      await captureScreenshot(projectId).unwrap();
    } catch (err) {
      console.error('Failed to capture screenshot:', err);
    }
  };

  const handleDeleteProject = async () => {
    try {
      await deleteProject(projectId).unwrap();
      navigate('/projects');
    } catch (err) {
      console.error('Failed to delete project:', err);
      setIsDeleteModalOpen(false);
    }
  };

  if (isLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>Loading project...</div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          <p>Project not found</p>
          <Button onClick={() => navigate('/projects')}>
            <ArrowLeft size={16} />
            Back to Projects
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Button
          variant="ghost"
          onClick={() => navigate('/projects')}
          className={styles.backButton}
        >
          <ArrowLeft size={20} />
          Back to Projects
        </Button>
        <Button
          variant="danger"
          size="small"
          onClick={() => setIsDeleteModalOpen(true)}
        >
          <Trash2 size={16} />
          Delete Project
        </Button>
      </div>

      <div className={styles.content}>
        <Card>
          <div className={styles.projectInfo}>
            <div className={styles.projectDetails}>
              <div className={styles.projectTitle}>
                <h1>{project.name}</h1>
                <Badge variant="primary">{project.state_code}</Badge>
              </div>
              {project.description && (
                <p className={styles.description}>{project.description}</p>
              )}

              <div className={styles.metadata}>
                <div className={styles.metadataItem}>
                  <MapPin size={16} />
                  <span>State: {project.state_code}</span>
                </div>
                <div className={styles.metadataItem}>
                  <Calendar size={16} />
                  <span>
                    Created: {new Date(project.created_at).toLocaleDateString()}
                  </span>
                </div>
                {project.base_url && (
                  <div className={styles.metadataItem}>
                    <ExternalLink size={16} />
                    <a
                      href={project.base_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={styles.link}
                    >
                      {project.base_url}
                    </a>
                  </div>
                )}
              </div>

              <div className={styles.stats}>
                <div className={styles.stat}>
                  <span className={styles.statValue}>{summary?.total_urls ?? 0}</span>
                  <span className={styles.statLabel}>URLs Monitored</span>
                </div>
                <div className={styles.stat}>
                  <span className={styles.statValue}>{summary?.total_checks ?? 0}</span>
                  <span className={styles.statLabel}>Checks Performed</span>
                </div>
                <div className={styles.stat}>
                  <span className={styles.statValue}>
                    {summary?.avg_score ? `${summary.avg_score.toFixed(1)}%` : '-'}
                  </span>
                  <span className={styles.statLabel}>Avg. Compliance</span>
                </div>
              </div>
            </div>

            {project.base_url && (
              <div className={styles.projectPreview}>
                {project.screenshot_path ? (
                  <div className={styles.screenshotContainer}>
                    <div className={styles.screenshot}>
                      <img
                        src={`${import.meta.env.VITE_API_URL}/${project.screenshot_path}`}
                        alt={`${project.name} screenshot`}
                      />
                    </div>
                    <div className={styles.screenshotOverlay}>
                      <Button
                        variant="secondary"
                        size="small"
                        onClick={handleCaptureScreenshot}
                        disabled={isCapturing}
                      >
                        <Camera size={16} />
                        {isCapturing ? 'Updating...' : 'Update'}
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className={styles.screenshotPlaceholder}>
                    <Camera size={48} />
                    <p>No screenshot</p>
                    <div className={styles.placeholderOverlay}>
                      <Button
                        variant="primary"
                        size="small"
                        onClick={handleCaptureScreenshot}
                        disabled={isCapturing}
                      >
                        <Camera size={16} />
                        {isCapturing ? 'Capturing...' : 'Capture'}
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </Card>

        <Card>
          <div className={styles.urlsSection}>
            <div className={styles.urlsHeader}>
              <h2>Monitored URLs</h2>
              <Button variant="primary" size="small" onClick={() => setIsAddURLModalOpen(true)}>
                <Plus size={16} />
                Add URL
              </Button>
            </div>
            <URLList projectId={projectId} />
          </div>
        </Card>
      </div>

      <AddURLModal
        isOpen={isAddURLModalOpen}
        onClose={() => setIsAddURLModalOpen(false)}
        projectId={projectId}
      />

      <ConfirmModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onConfirm={handleDeleteProject}
        title="Delete Project"
        message={`Are you sure you want to delete "${project?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        isLoading={isDeleting}
      />
    </div>
  );
};
