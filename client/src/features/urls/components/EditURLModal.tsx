import React, { useState, useEffect } from 'react';
import { Modal } from '@components/ui/Modal';
import { Button } from '@components/ui/Button';
import { Toggle } from '@components/ui/Toggle';
import { useAlert } from '@contexts/AlertContext';
import type { MonitoredURL } from '../urlsApi';
import styles from './EditURLModal.module.scss';

interface EditURLModalProps {
  url: MonitoredURL;
  isOpen: boolean;
  onClose: () => void;
  onSave: (id: number, data: Partial<MonitoredURL>) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
}

const URL_TYPES = [
  { value: 'HOMEPAGE', label: 'Homepage' },
  { value: 'VDP', label: 'Vehicle Detail Page (VDP)' },
  { value: 'INVENTORY', label: 'Inventory Listing' },
  { value: 'SRP', label: 'Search Results Page' },
];

const EditURLModal: React.FC<EditURLModalProps> = ({ url, isOpen, onClose, onSave, onDelete }) => {
  const [urlType, setUrlType] = useState(url.url_type);
  const [checkFrequency, setCheckFrequency] = useState(url.check_frequency_hours);
  const [active, setActive] = useState(url.active);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const { showConfirm } = useAlert();

  // Update form when URL changes
  useEffect(() => {
    setUrlType(url.url_type);
    setCheckFrequency(url.check_frequency_hours);
    setActive(url.active);
  }, [url]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSave(url.id, {
        url_type: urlType,
        check_frequency_hours: checkFrequency,
        active: active,
      });
      onClose();
    } catch (error) {
      console.error('Failed to update URL:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    const confirmed = await showConfirm({
      title: 'Delete URL',
      message: 'Are you sure you want to delete this URL? This action cannot be undone.',
      confirmText: 'Delete',
      variant: 'danger',
    });

    if (!confirmed) return;

    setIsDeleting(true);
    try {
      await onDelete(url.id);
      onClose();
    } catch (error) {
      console.error('Failed to delete URL:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="medium" title="Edit URL Settings">
      <div className={styles.modal}>

        <div className={styles.urlDisplay}>
          <label>URL</label>
          <div className={styles.urlText}>{url.url}</div>
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="urlType">Page Type</label>
          <select
            id="urlType"
            value={urlType}
            onChange={(e) => setUrlType(e.target.value)}
            className={styles.select}
          >
            {URL_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          <p className={styles.helpText}>
            Determines which compliance rules apply to this page
          </p>
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="checkFrequency">Check Frequency (hours)</label>
          <input
            id="checkFrequency"
            type="number"
            min="1"
            max="168"
            value={checkFrequency}
            onChange={(e) => setCheckFrequency(parseInt(e.target.value))}
            className={styles.input}
          />
          <p className={styles.helpText}>
            How often to automatically scan this URL (1-168 hours)
          </p>
        </div>

        <div className={styles.formGroup}>
          <div className={styles.toggleRow}>
            <label>Active (enable automatic scanning)</label>
            <Toggle
              checked={active}
              onChange={() => setActive(!active)}
              size="small"
            />
          </div>
        </div>

        {url.platform && (
          <div className={styles.infoSection}>
            <label>Detected Platform</label>
            <div className={styles.infoValue}>{url.platform}</div>
          </div>
        )}

        {url.template_id && (
          <div className={styles.infoSection}>
            <label>Template ID</label>
            <div className={styles.infoValue}>{url.template_id}</div>
          </div>
        )}

        <div className={styles.actions}>
          <div className={styles.deleteSection}>
            <Button
              variant="danger"
              onClick={handleDelete}
              disabled={isSaving || isDeleting}
            >
              {isDeleting ? 'Deleting...' : 'Delete URL'}
            </Button>
          </div>
          <div className={styles.mainActions}>
            <Button variant="secondary" onClick={onClose} disabled={isSaving || isDeleting}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={isSaving || isDeleting}>
              {isSaving ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default EditURLModal;
