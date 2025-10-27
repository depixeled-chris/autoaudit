import { useState, useEffect } from 'react';
import { useUpdateRuleMutation, type Rule } from '@services/api/rulesApi';
import { useGetLegislationSourceQuery } from '@services/api/statesApi';
import { Modal } from '@components/ui/Modal/Modal';
import { Toggle } from '@components/ui/Toggle/Toggle';
import { useAlert } from '@contexts/AlertContext';
import styles from './Modal.module.scss';

interface Props {
  rule: Rule;
  onClose: () => void;
}

export default function RuleDetailModal({ rule, onClose }: Props) {
  const [ruleText, setRuleText] = useState(rule.rule_text);
  const [pageTypes, setPageTypes] = useState(rule.applies_to_page_types || '');
  const [active, setActive] = useState(rule.active);
  const [approved, setApproved] = useState(rule.approved);
  const [hasChanges, setHasChanges] = useState(false);
  const { showAlert } = useAlert();

  const [updateRule, { isLoading: isSaving }] = useUpdateRuleMutation();

  // Fetch linked legislation source if available
  const { data: legislationSource } = useGetLegislationSourceQuery(
    rule.legislation_source_id!,
    {
      skip: !rule.legislation_source_id,
    }
  );

  useEffect(() => {
    const changed =
      ruleText !== rule.rule_text ||
      pageTypes !== (rule.applies_to_page_types || '') ||
      active !== rule.active ||
      approved !== rule.approved;
    setHasChanges(changed);
  }, [ruleText, pageTypes, active, approved, rule]);

  const handleSave = async () => {
    try {
      await updateRule({
        id: rule.id,
        data: {
          rule_text: ruleText,
          applies_to_page_types: pageTypes || null,
          active,
          approved,
        },
      }).unwrap();
      onClose();
    } catch (error: any) {
      console.error('Failed to update rule:', error);
      showAlert({
        type: 'error',
        title: 'Update Failed',
        message: error.data?.detail || error.message || 'Failed to update rule. Please try again.',
      });
    }
  };

  const handleToggleApproval = () => {
    setApproved(!approved);
  };

  return (
    <Modal isOpen={true} onClose={onClose} title="Rule Details" size="large">
      <div className={styles.content}>
        {legislationSource && (
          <div className={styles.field}>
            <label>Linked Legislation Source</label>
            <div className={styles.legislationInfo}>
              <div className={styles.statuteNumber}>
                {legislationSource.statute_number}
              </div>
              <div className={styles.title}>{legislationSource.title}</div>
            </div>
          </div>
        )}

        <div className={styles.field}>
          <label>Rule Text</label>
          <textarea
            value={ruleText}
            onChange={(e) => setRuleText(e.target.value)}
            className={styles.textarea}
            rows={8}
          />
        </div>

        <div className={styles.field}>
          <label>Applies to Page Types</label>
          <input
            type="text"
            value={pageTypes}
            onChange={(e) => setPageTypes(e.target.value)}
            placeholder="e.g., homepage, inventory, finance"
            className={styles.input}
          />
          <p className={styles.helpText}>
            Comma-separated list of page type codes this rule applies to. Leave empty for
            universal rules.
          </p>
        </div>

        <div className={styles.fieldRow}>
          <div className={styles.field}>
            <label>Active Status</label>
            <div className={styles.toggleRow}>
              <span className={styles.toggleLabel}>
                {active ? 'Active' : 'Inactive'}
              </span>
              <Toggle checked={active} onChange={setActive} />
            </div>
            <p className={styles.helpText}>
              Only active rules are used in compliance checks
            </p>
          </div>

          <div className={styles.field}>
            <label>Approval Status</label>
            <div className={styles.toggleRow}>
              <span className={styles.toggleLabel}>
                {approved ? 'Approved' : 'Not Approved'}
              </span>
              <button
                onClick={handleToggleApproval}
                className={approved ? styles.approvedButton : styles.unapprovedButton}
              >
                {approved ? 'Unapprove' : 'Approve'}
              </button>
            </div>
            <p className={styles.helpText}>
              Unapproved rules need review before being used in production
            </p>
          </div>
        </div>

        <div className={styles.metadata}>
          <div className={styles.metadataItem}>
            <span className={styles.metadataLabel}>State:</span>
            <span className={styles.metadataValue}>{rule.state_code}</span>
          </div>
          <div className={styles.metadataItem}>
            <span className={styles.metadataLabel}>Status:</span>
            <span className={styles.metadataValue}>{rule.status}</span>
          </div>
          {rule.is_manually_modified && (
            <div className={styles.metadataItem}>
              <span className={styles.metadataLabel}>Modified:</span>
              <span className={styles.metadataValue} title="This rule has been manually edited">
                ✏️ Manually Edited
              </span>
            </div>
          )}
          {rule.original_rule_text && rule.is_manually_modified && (
            <div className={styles.metadataItem}>
              <span className={styles.metadataLabel}>Original AI Text:</span>
              <span className={styles.metadataValue} title={rule.original_rule_text}>
                {rule.original_rule_text.substring(0, 60)}...
              </span>
            </div>
          )}
          <div className={styles.metadataItem}>
            <span className={styles.metadataLabel}>Created:</span>
            <span className={styles.metadataValue}>
              {new Date(rule.created_at).toLocaleString()}
            </span>
          </div>
          <div className={styles.metadataItem}>
            <span className={styles.metadataLabel}>Updated:</span>
            <span className={styles.metadataValue}>
              {new Date(rule.updated_at).toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      <div className={styles.actions}>
        <button onClick={onClose} className={styles.secondaryButton}>
          Cancel
        </button>
        <button
          onClick={handleSave}
          className={styles.primaryButton}
          disabled={!hasChanges || isSaving}
        >
          {isSaving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </Modal>
  );
}
