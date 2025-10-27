import { useState } from 'react';
import { useCreatePreambleVersionMutation } from '@services/api/preamblesApi';
import styles from './Modal.module.scss';

interface Props {
  preambleId: number;
  onClose: () => void;
}

export default function CreateVersionModal({ preambleId, onClose }: Props) {
  const [preambleText, setPreambleText] = useState('');
  const [changeSummary, setChangeSummary] = useState('');
  const [createVersion, { isLoading }] = useCreatePreambleVersionMutation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createVersion({
        preambleId,
        data: { preamble_id: preambleId, preamble_text: preambleText, change_summary: changeSummary },
      }).unwrap();
      onClose();
    } catch (error) {
      console.error('Failed:', error);
    }
  };

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={`${styles.modal} ${styles.large}`} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h2>Create New Version</h2>
          <button className={styles.closeButton} onClick={onClose}>×</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className={styles.formGroup}>
            <label>Change Summary *</label>
            <input
              value={changeSummary}
              onChange={(e) => setChangeSummary(e.target.value)}
              placeholder="What changed in this version?"
              required
            />
          </div>
          <div className={styles.formGroup}>
            <label>Preamble Text *</label>
            <textarea
              value={preambleText}
              onChange={(e) => setPreambleText(e.target.value)}
              placeholder="Enter the updated preamble text..."
              rows={15}
              required
            />
            <small>New versions start as draft. Activate to make them live.</small>
          </div>
          <div className={styles.actions}>
            <button type="button" className={styles.secondaryButton} onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className={styles.primaryButton} disabled={isLoading}>
              {isLoading ? 'Creating...' : 'Create Draft Version'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
