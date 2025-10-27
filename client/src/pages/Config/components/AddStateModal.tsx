import { useState } from 'react';
import { useCreateStateMutation } from '@services/api/statesApi';
import styles from './Modal.module.scss';

interface AddStateModalProps {
  onClose: () => void;
}

export default function AddStateModal({ onClose }: AddStateModalProps) {
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [createState, { isLoading }] = useCreateStateMutation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createState({ code: code.toUpperCase(), name, active: true }).unwrap();
      onClose();
    } catch (error) {
      console.error('Failed to create state:', error);
    }
  };

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h2>Add State</h2>
          <button className={styles.closeButton} onClick={onClose}>×</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className={styles.formGroup}>
            <label>State Code (2 letters)</label>
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value.slice(0, 2))}
              placeholder="OK"
              maxLength={2}
              required
            />
          </div>
          <div className={styles.formGroup}>
            <label>State Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Oklahoma"
              required
            />
          </div>
          <div className={styles.actions}>
            <button type="button" className={styles.secondaryButton} onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className={styles.primaryButton} disabled={isLoading}>
              {isLoading ? 'Adding...' : 'Add State'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
