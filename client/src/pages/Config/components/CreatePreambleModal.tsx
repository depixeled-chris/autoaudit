import { useState } from 'react';
import { useCreatePreambleMutation } from '@services/api/preamblesApi';
import styles from './Modal.module.scss';

interface Props {
  onClose: () => void;
}

export default function CreatePreambleModal({ onClose }: Props) {
  const [form, setForm] = useState({
    name: '',
    scope: 'universal' as 'universal' | 'state' | 'page_type' | 'project',
    state_code: '',
    page_type_code: '',
    initial_text: '',
  });
  const [createPreamble, { isLoading }] = useCreatePreambleMutation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createPreamble({
        ...form,
        state_code: form.state_code || undefined,
        page_type_code: form.page_type_code || undefined,
        created_via: 'config',
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
          <h2>Create Preamble</h2>
          <button className={styles.closeButton} onClick={onClose}>×</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className={styles.formGroup}>
            <label>Name *</label>
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Universal Compliance Principles"
              required
            />
          </div>
          <div className={styles.formGroup}>
            <label>Scope *</label>
            <select
              value={form.scope}
              onChange={(e) => setForm({ ...form, scope: e.target.value as any })}
              required
            >
              <option value="universal">Universal</option>
              <option value="state">State</option>
              <option value="page_type">Page Type</option>
              <option value="project">Project</option>
            </select>
          </div>
          {(form.scope === 'state' || form.scope === 'page_type') && (
            <div className={styles.formGroup}>
              <label>State Code</label>
              <input
                value={form.state_code}
                onChange={(e) => setForm({ ...form, state_code: e.target.value.toUpperCase() })}
                placeholder="OK"
                maxLength={2}
              />
            </div>
          )}
          {(form.scope === 'page_type' || form.scope === 'project') && (
            <div className={styles.formGroup}>
              <label>Page Type Code</label>
              <input
                value={form.page_type_code}
                onChange={(e) => setForm({ ...form, page_type_code: e.target.value })}
                placeholder="VDP, HOMEPAGE, etc."
              />
            </div>
          )}
          <div className={styles.formGroup}>
            <label>Initial Preamble Text *</label>
            <textarea
              value={form.initial_text}
              onChange={(e) => setForm({ ...form, initial_text: e.target.value })}
              placeholder="Enter the preamble guidance text..."
              rows={12}
              required
            />
          </div>
          <div className={styles.actions}>
            <button type="button" className={styles.secondaryButton} onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className={styles.primaryButton} disabled={isLoading}>
              {isLoading ? 'Creating...' : 'Create Preamble'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
