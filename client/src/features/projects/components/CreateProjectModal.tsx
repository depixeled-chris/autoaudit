import { useState, FormEvent } from 'react';
import { Modal } from '@components/ui/Modal';
import { Input, Textarea } from '@components/ui/Input';
import { Button } from '@components/ui/Button';
import { useCreateProjectMutation } from '../projectsApi';
import styles from './CreateProjectModal.module.scss';

export interface CreateProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CreateProjectModal({ isOpen, onClose }: CreateProjectModalProps) {
  const [createProject, { isLoading }] = useCreateProjectMutation();
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

  const handleClose = () => {
    setFormData({ name: '', state_code: '', description: '', base_url: '' });
    setErrors({});
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Create New Project" size="medium">
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
    </Modal>
  );
}
