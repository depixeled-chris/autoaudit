import { useState } from 'react';
import { Modal } from '@components/ui/Modal';
import { Button } from '@components/ui/Button';
import { Input } from '@components/ui/Input';
import { useCreateURLMutation } from '../urlsApi';
import styles from './AddURLModal.module.scss';

interface AddURLModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: number;
}

export const AddURLModal = ({ isOpen, onClose, projectId }: AddURLModalProps) => {
  const [createURL, { isLoading }] = useCreateURLMutation();
  const [formData, setFormData] = useState({
    url: '',
    url_type: 'vdp',
    platform: '',
    template_id: '',
    check_frequency_hours: 24,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await createURL({
        ...formData,
        project_id: projectId,
        platform: formData.platform || undefined,
        template_id: formData.template_id || undefined,
      }).unwrap();

      // Reset form and close modal
      setFormData({
        url: '',
        url_type: 'vdp',
        platform: '',
        template_id: '',
        check_frequency_hours: 24,
      });
      onClose();
    } catch (error) {
      console.error('Failed to create URL:', error);
    }
  };

  const handleClose = () => {
    setFormData({
      url: '',
      url_type: 'vdp',
      platform: '',
      template_id: '',
      check_frequency_hours: 24,
    });
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Add URL to Monitor">
      <form onSubmit={handleSubmit} className={styles.form}>
        <Input
          label="URL"
          type="url"
          value={formData.url}
          onChange={(e) => setFormData({ ...formData, url: e.target.value })}
          placeholder="https://example.com/page"
          required
        />

        <div className={styles.row}>
          <div className={styles.field}>
            <label htmlFor="url_type">Page Type</label>
            <select
              id="url_type"
              value={formData.url_type}
              onChange={(e) => setFormData({ ...formData, url_type: e.target.value })}
              className={styles.select}
            >
              <option value="vdp">VDP (Vehicle Detail Page)</option>
              <option value="homepage">Homepage</option>
              <option value="inventory">Inventory</option>
              <option value="other">Other</option>
            </select>
          </div>

          <Input
            label="Check Frequency (hours)"
            type="number"
            value={formData.check_frequency_hours}
            onChange={(e) =>
              setFormData({ ...formData, check_frequency_hours: parseInt(e.target.value) })
            }
            min={1}
            max={168}
            required
          />
        </div>

        <div className={styles.row}>
          <Input
            label="Platform (optional)"
            type="text"
            value={formData.platform}
            onChange={(e) => setFormData({ ...formData, platform: e.target.value })}
            placeholder="dealer.com, DealerOn, etc."
          />

          <Input
            label="Template ID (optional)"
            type="text"
            value={formData.template_id}
            onChange={(e) => setFormData({ ...formData, template_id: e.target.value })}
            placeholder="dealer.com_vdp"
          />
        </div>

        <div className={styles.actions}>
          <Button type="button" variant="secondary" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" disabled={isLoading}>
            {isLoading ? 'Adding...' : 'Add URL'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
