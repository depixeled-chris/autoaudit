import { useState } from 'react';
import { Trash2, Plus, Settings } from 'lucide-react';
import {
  useGetPageTypesQuery,
  useUpdatePageTypeMutation,
  useDeletePageTypeMutation,
  useCreatePageTypeMutation,
  type PageType
} from '../pageTypesApi';
import { Button } from '@components/ui/Button';
import { Toggle } from '@components/ui/Toggle';
import { ToastContainer } from '@components/ui/Toast';
import { useToast } from '@hooks/useToast';
import { PageTypeSettingsModal } from './PageTypeSettingsModal';
import styles from './PageTypesTable.module.scss';

export const PageTypesTable = () => {
  const { data: pageTypes, isLoading } = useGetPageTypesQuery({ activeOnly: false });
  const [updatePageType] = useUpdatePageTypeMutation();
  const [deletePageType] = useDeletePageTypeMutation();
  const [createPageType] = useCreatePageTypeMutation();
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editValues, setEditValues] = useState<{ name: string; description: string }>({ name: '', description: '' });
  const [isCreating, setIsCreating] = useState(false);
  const [newPageType, setNewPageType] = useState({ code: '', name: '', description: '' });
  const [settingsPageType, setSettingsPageType] = useState<PageType | null>(null);
  const { toasts, removeToast, success, error } = useToast();

  const handleToggleActive = async (pageType: PageType) => {
    try {
      await updatePageType({ id: pageType.id, data: { active: !pageType.active } }).unwrap();
      success(`Page type ${!pageType.active ? 'activated' : 'deactivated'}`);
    } catch (err: any) {
      console.error('Failed to toggle page type active status:', err);
      error(err?.data?.detail || 'Failed to update page type');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this page type? This action cannot be undone.')) {
      return;
    }

    try {
      await deletePageType(id).unwrap();
      success('Page type deleted successfully');
    } catch (err: any) {
      console.error('Failed to delete page type:', err);
      error(err?.data?.detail || 'Failed to delete page type');
    }
  };

  const handleStartEdit = (pageType: PageType) => {
    setEditingId(pageType.id);
    setEditValues({ name: pageType.name, description: pageType.description || '' });
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditValues({ name: '', description: '' });
  };

  const handleSaveEdit = async (id: number) => {
    try {
      await updatePageType({
        id,
        data: {
          name: editValues.name,
          description: editValues.description || undefined
        }
      }).unwrap();
      success('Page type updated successfully');
      setEditingId(null);
    } catch (err: any) {
      console.error('Failed to update page type:', err);
      error(err?.data?.detail || 'Failed to update page type');
    }
  };

  const handleCreatePageType = async () => {
    if (!newPageType.code || !newPageType.name) {
      error('Code and name are required');
      return;
    }

    try {
      await createPageType({
        code: newPageType.code.toUpperCase(),
        name: newPageType.name,
        description: newPageType.description || undefined
      }).unwrap();
      success('Page type created successfully');
      setIsCreating(false);
      setNewPageType({ code: '', name: '', description: '' });
    } catch (err: any) {
      console.error('Failed to create page type:', err);
      error(err?.data?.detail || 'Failed to create page type');
    }
  };

  if (isLoading) {
    return <div className={styles.loading}>Loading page types...</div>;
  }

  return (
    <>
      <ToastContainer toasts={toasts} onRemove={removeToast} />

      <div className={styles.tableHeader}>
        <Button
          onClick={() => setIsCreating(!isCreating)}
          size="small"
          variant={isCreating ? 'secondary' : 'primary'}
        >
          <Plus size={16} />
          {isCreating ? 'Cancel' : 'Add Page Type'}
        </Button>
      </div>

      {isCreating && (
        <div className={styles.createForm}>
          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label>Code *</label>
              <input
                type="text"
                value={newPageType.code}
                onChange={(e) => setNewPageType({ ...newPageType, code: e.target.value.toUpperCase() })}
                placeholder="e.g., CONTACT_US"
                className={styles.input}
              />
              <span className={styles.helpText}>Unique identifier (uppercase)</span>
            </div>
            <div className={styles.formGroup}>
              <label>Name *</label>
              <input
                type="text"
                value={newPageType.name}
                onChange={(e) => setNewPageType({ ...newPageType, name: e.target.value })}
                placeholder="e.g., Contact Us Page"
                className={styles.input}
              />
            </div>
          </div>
          <div className={styles.formGroup}>
            <label>Description</label>
            <input
              type="text"
              value={newPageType.description}
              onChange={(e) => setNewPageType({ ...newPageType, description: e.target.value })}
              placeholder="Optional description"
              className={styles.input}
            />
          </div>
          <div className={styles.formActions}>
            <Button onClick={handleCreatePageType} size="small">
              Create Page Type
            </Button>
          </div>
        </div>
      )}

      <div className={styles.tableContainer}>
        <table className={styles.pageTypesTable}>
          <thead>
            <tr>
              <th>Code</th>
              <th>Name</th>
              <th>Description</th>
              <th>Active</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {pageTypes?.map((pageType) => (
              <tr key={pageType.id} className={!pageType.active ? styles.inactive : ''}>
                <td className={styles.codeCell}>
                  <code>{pageType.code}</code>
                </td>
                <td className={styles.nameCell}>
                  {editingId === pageType.id ? (
                    <input
                      type="text"
                      value={editValues.name}
                      onChange={(e) => setEditValues({ ...editValues, name: e.target.value })}
                      className={styles.inlineInput}
                      autoFocus
                    />
                  ) : (
                    <span onClick={() => handleStartEdit(pageType)} className={styles.editable}>
                      {pageType.name}
                    </span>
                  )}
                </td>
                <td className={styles.descriptionCell}>
                  {editingId === pageType.id ? (
                    <input
                      type="text"
                      value={editValues.description}
                      onChange={(e) => setEditValues({ ...editValues, description: e.target.value })}
                      className={styles.inlineInput}
                      placeholder="Optional description"
                    />
                  ) : (
                    <span
                      onClick={() => handleStartEdit(pageType)}
                      className={`${styles.editable} ${!pageType.description ? styles.emptyCell : ''}`}
                    >
                      {pageType.description || '—'}
                    </span>
                  )}
                </td>
                <td onClick={(e) => e.stopPropagation()}>
                  <Toggle
                    checked={pageType.active}
                    onChange={() => handleToggleActive(pageType)}
                    size="small"
                  />
                </td>
                <td className={styles.actionsCell}>
                  {editingId === pageType.id ? (
                    <div className={styles.editActions}>
                      <Button variant="primary" size="small" onClick={() => handleSaveEdit(pageType.id)}>
                        Save
                      </Button>
                      <Button variant="secondary" size="small" onClick={handleCancelEdit}>
                        Cancel
                      </Button>
                    </div>
                  ) : (
                    <div className={styles.actionButtons}>
                      <Button
                        variant="ghost"
                        size="small"
                        onClick={() => setSettingsPageType(pageType)}
                        title="Settings"
                      >
                        <Settings size={16} />
                      </Button>
                      <Button
                        variant="ghost"
                        size="small"
                        onClick={() => handleDelete(pageType.id)}
                        title="Delete"
                      >
                        <Trash2 size={16} />
                      </Button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {settingsPageType && (
        <PageTypeSettingsModal
          pageType={settingsPageType}
          isOpen={true}
          onClose={() => setSettingsPageType(null)}
          onSuccess={() => success('Page type settings updated successfully')}
        />
      )}
    </>
  );
};
