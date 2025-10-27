import { useState, FormEvent } from 'react';
import { Modal } from '@components/ui/Modal';
import { Input, Textarea } from '@components/ui/Input';
import { Button } from '@components/ui/Button';
import { useCreateProjectMutation, projectsApi } from '../projectsApi';
import { useDispatch } from 'react-redux';
import { Loader2, Sparkles } from 'lucide-react';
import apiClient from '@lib/api/axios';
import styles from './CreateProjectModal.module.scss';

export interface CreateProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type SetupMode = 'intelligent' | 'manual';

export function CreateProjectModal({ isOpen, onClose }: CreateProjectModalProps) {
  const dispatch = useDispatch();
  const [createProject, { isLoading }] = useCreateProjectMutation();
  const [mode, setMode] = useState<SetupMode>('intelligent');
  const [intelligentUrl, setIntelligentUrl] = useState('');
  const [setupStatus, setSetupStatus] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    state_code: '',
    description: '',
    base_url: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Project name is required';
    }

    if (!formData.state_code.trim()) {
      newErrors.state_code = 'State code is required';
    } else if (formData.state_code.length !== 2) {
      newErrors.state_code = 'State code must be 2 characters (e.g., CA, NY)';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    try {
      await createProject({
        name: formData.name,
        state_code: formData.state_code.toUpperCase(),
        description: formData.description || undefined,
        base_url: formData.base_url || undefined,
      }).unwrap();

      // Reset form and close modal
      setFormData({ name: '', state_code: '', description: '', base_url: '' });
      setErrors({});
      onClose();
    } catch (error) {
      console.error('Failed to create project:', error);
      setErrors({ submit: 'Failed to create project. Please try again.' });
    }
  };

  const handleIntelligentSetup = async (e: FormEvent) => {
    e.preventDefault();

    if (!intelligentUrl.trim()) {
      setErrors({ url: 'URL is required' });
      return;
    }

    setIsAnalyzing(true);
    setSetupStatus('Analyzing website...');
    setErrors({});

    try {
      const response = await apiClient.post('/api/projects/intelligent-setup', {
        url: intelligentUrl,
      });

      console.log('Intelligent setup result:', response.data);

      // Invalidate projects cache to refresh the list
      dispatch(projectsApi.util.invalidateTags(['Project']));

      setIntelligentUrl('');
      setSetupStatus('');
      setErrors({});
      onClose();
    } catch (error: any) {
      console.error('Intelligent setup failed:', error);

      let errorMessage = 'Setup failed. Please try manual mode.';

      // Check for specific error messages in order of priority
      if (error.response?.data?.error) {
        // Custom exception handler sends errors in 'error' field
        errorMessage = error.response.data.error;
      } else if (error.response?.data?.detail) {
        // FastAPI default sends errors in 'detail' field
        errorMessage = error.response.data.detail;
      } else if (error.response?.data?.message) {
        // Some APIs send errors in 'message' field
        errorMessage = error.response.data.message;
      } else if (typeof error.response?.data === 'string') {
        // Some APIs send error as string
        errorMessage = error.response.data;
      } else if (error.message && error.message !== 'Request failed with status code 400') {
        // Use axios error message if it's not generic
        errorMessage = error.message;
      }

      // Check if it's a "no rules" or "no legislation" error and provide helpful guidance
      if (errorMessage.toLowerCase().includes('no rules') ||
          errorMessage.toLowerCase().includes('no legislation') ||
          errorMessage.toLowerCase().includes('no active compliance') ||
          (errorMessage.toLowerCase().includes('state') && errorMessage.toLowerCase().includes('not configured'))) {
        errorMessage = 'This state has no compliance rules configured yet. Please go to Config → States to upload legislation and generate rules first.';
      }

      setErrors({ submit: errorMessage });
      setSetupStatus('');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleClose = () => {
    setFormData({ name: '', state_code: '', description: '', base_url: '' });
    setIntelligentUrl('');
    setSetupStatus('');
    setErrors({});
    setMode('intelligent');
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Create New Project" size="medium">
      <div className={styles.modeSelector}>
        <button
          type="button"
          className={`${styles.modeButton} ${mode === 'intelligent' ? styles.active : ''}`}
          onClick={() => setMode('intelligent')}
        >
          <Sparkles size={16} />
          Intelligent Setup
        </button>
        <button
          type="button"
          className={`${styles.modeButton} ${mode === 'manual' ? styles.active : ''}`}
          onClick={() => setMode('manual')}
        >
          Manual Setup
        </button>
      </div>

      {mode === 'intelligent' ? (
        <form onSubmit={handleIntelligentSetup} className={styles.form}>
          <div className={styles.intelligentInfo}>
            <p>Enter any dealership website URL. We'll automatically detect:</p>
            <ul>
              <li>Dealership name and location</li>
              <li>Homepage and inventory pages</li>
              <li>Sample vehicle listings</li>
              <li>Recommended check frequencies</li>
            </ul>
          </div>

          <Input
            id="intelligent-url"
            label="Website URL"
            value={intelligentUrl}
            onChange={(e) => setIntelligentUrl(e.target.value)}
            error={errors.url}
            placeholder="https://www.dealership.com"
            type="url"
            required
            disabled={isAnalyzing}
          />

          {setupStatus && (
            <div className={styles.setupStatus}>
              <Loader2 className={styles.spinner} size={16} />
              {setupStatus}
            </div>
          )}

          {errors.submit && <div className={styles.submitError}>{errors.submit}</div>}

          <div className={styles.actions}>
            <Button type="button" variant="secondary" onClick={handleClose} disabled={isAnalyzing}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={isAnalyzing}>
              {isAnalyzing ? 'Analyzing...' : 'Start Intelligent Setup'}
            </Button>
          </div>
        </form>
      ) : (
        <form onSubmit={handleSubmit} className={styles.form}>
        <Input
          id="name"
          label="Project Name"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          error={errors.name}
          placeholder="Enter project name"
          required
        />

        <Input
          id="state_code"
          label="State Code"
          value={formData.state_code}
          onChange={(e) => setFormData({ ...formData, state_code: e.target.value })}
          error={errors.state_code}
          placeholder="CA, NY, TX, etc."
          maxLength={2}
          required
        />

        <Input
          id="base_url"
          label="Base URL (Optional)"
          value={formData.base_url}
          onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
          error={errors.base_url}
          placeholder="https://example.com"
          type="url"
        />

        <Textarea
          id="description"
          label="Description (Optional)"
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          placeholder="Enter project description"
          rows={4}
        />

        {errors.submit && <div className={styles.submitError}>{errors.submit}</div>}

          <div className={styles.actions}>
            <Button type="button" variant="secondary" onClick={handleClose} disabled={isLoading}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={isLoading}>
              {isLoading ? 'Creating...' : 'Create Project'}
            </Button>
          </div>
        </form>
      )}
    </Modal>
  );
}
