import { useState, useEffect } from 'react';
import { Modal } from '@components/ui/Modal';
import { Button } from '@components/ui/Button';
import { Toggle } from '@components/ui/Toggle';
import { useUpdatePageTypeMutation, type PageType } from '../pageTypesApi';
import styles from './PageTypeSettingsModal.module.scss';

interface PageTypeSettingsModalProps {
  pageType: PageType;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const PageTypeSettingsModal = ({ pageType, isOpen, onClose, onSuccess }: PageTypeSettingsModalProps) => {
  const [updatePageType] = useUpdatePageTypeMutation();
  const [isSaving, setIsSaving] = useState(false);

  const [preamble, setPreamble] = useState(pageType.preamble || '');
  const [extractionTemplate, setExtractionTemplate] = useState(pageType.extraction_template || '');
  const [requiresLlmConfirmation, setRequiresLlmConfirmation] = useState(pageType.requires_llm_visual_confirmation);
  const [requiresHumanConfirmation, setRequiresHumanConfirmation] = useState(pageType.requires_human_confirmation);

  // Reset form when pageType changes
  useEffect(() => {
    setPreamble(pageType.preamble || '');
    setExtractionTemplate(pageType.extraction_template || '');
    setRequiresLlmConfirmation(pageType.requires_llm_visual_confirmation);
    setRequiresHumanConfirmation(pageType.requires_human_confirmation);
  }, [pageType]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await updatePageType({
        id: pageType.id,
        data: {
          preamble: preamble || undefined,
          extraction_template: extractionTemplate || undefined,
          requires_llm_visual_confirmation: requiresLlmConfirmation,
          requires_human_confirmation: requiresHumanConfirmation,
        },
      }).unwrap();
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Failed to update page type settings:', error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      size="large"
      title={`${pageType.name} Settings`}
    >
      <div className={styles.content}>
        <div className={styles.section}>
          <h3>Analysis Preamble</h3>
          <p className={styles.helpText}>
            This text is sent to the LLM before analyzing pages of this type. It provides context and
            instructions for what to look for during compliance checks.
          </p>
          <textarea
            value={preamble}
            onChange={(e) => setPreamble(e.target.value)}
            className={styles.textarea}
            rows={5}
            placeholder="e.g., Analyze this page for automotive dealership advertising compliance..."
          />
        </div>

        <div className={styles.section}>
          <h3>Data Extraction Template</h3>
          <p className={styles.helpText}>
            Define a JSON template for extracting structured data from pages of this type. This helps
            standardize what information is captured during analysis.
          </p>
          <textarea
            value={extractionTemplate}
            onChange={(e) => setExtractionTemplate(e.target.value)}
            className={styles.textarea}
            rows={8}
            placeholder={`e.g., {\n  "price": "",\n  "disclosures": [],\n  "finance_terms": {}\n}`}
          />
        </div>

        <div className={styles.section}>
          <h3>Confirmation Requirements</h3>
          <p className={styles.helpText}>
            Configure which types of confirmation are required for pages of this type.
          </p>

          <div className={styles.toggleGroup}>
            <div className={styles.toggleRow}>
              <div className={styles.toggleLabel}>
                <strong>LLM Visual Confirmation</strong>
                <span className={styles.toggleDescription}>
                  Require GPT-4V to analyze screenshots for spatial/visual compliance rules
                </span>
              </div>
              <Toggle
                checked={requiresLlmConfirmation}
                onChange={() => setRequiresLlmConfirmation(!requiresLlmConfirmation)}
                size="small"
              />
            </div>

            <div className={styles.toggleRow}>
              <div className={styles.toggleLabel}>
                <strong>Human Confirmation</strong>
                <span className={styles.toggleDescription}>
                  Flag pages of this type for manual human review before finalizing compliance status
                </span>
              </div>
              <Toggle
                checked={requiresHumanConfirmation}
                onChange={() => setRequiresHumanConfirmation(!requiresHumanConfirmation)}
                size="small"
              />
            </div>
          </div>
        </div>

        <div className={styles.actions}>
          <Button variant="secondary" onClick={onClose} disabled={isSaving}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? 'Saving...' : 'Save Settings'}
          </Button>
        </div>
      </div>
    </Modal>
  );
};
