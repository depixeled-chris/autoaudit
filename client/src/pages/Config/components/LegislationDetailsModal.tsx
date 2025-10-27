import { useState } from 'react';
import type { LegislationSource } from '@services/api/statesApi';
import {
  useGetRulesByLegislationQuery,
  useDigestLegislationMutation,
} from '@services/api/rulesApi';
import { Modal } from '@components/ui/Modal/Modal';
import { useAlert } from '@contexts/AlertContext';
import styles from './Modal.module.scss';

interface Props {
  legislation: LegislationSource;
  onClose: () => void;
}

export default function LegislationDetailsModal({ legislation, onClose }: Props) {
  console.log('LegislationDetailsModal rendering', { legislation });

  const [showRules, setShowRules] = useState(false);
  const { showAlert, showConfirm } = useAlert();

  const { data: rulesData, isLoading: rulesLoading } = useGetRulesByLegislationQuery(
    legislation.id,
    {
      skip: !showRules,
    }
  );
  const [digestLegislation, { isLoading: isDigesting }] = useDigestLegislationMutation();

  const rules = rulesData?.rules || [];

  console.log('LegislationDetailsModal state', { showRules, rulesLoading, rulesCount: rules.length });

  const handleReDigest = async () => {
    const hasRules = rules.length > 0;
    let confirmed = false;

    if (!hasRules) {
      // First digest - simple confirmation
      confirmed = await showConfirm({
        title: 'Digest Legislation',
        message: 'This will digest the legislation source to generate compliance rules using AI.\n\nContinue?',
        confirmText: 'Digest',
        variant: 'default',
      });
    } else {
      // Re-digest - show protection warning
      const protectedRules = rules.filter(r => r.approved || r.is_manually_modified);
      const unprotectedRules = rules.filter(r => !r.approved && !r.is_manually_modified);

      confirmed = await showConfirm({
        title: 'Re-digest Legislation',
        message:
          `Protected: ${protectedRules.length} approved/edited rules will be PRESERVED.\n` +
          `Deletable: ${unprotectedRules.length} unapproved rules will be deleted and regenerated.\n\n` +
          `Continue?`,
        confirmText: 'Re-digest',
        variant: 'warning',
      });
    }

    if (!confirmed) {
      return;
    }

    try {
      const result = await digestLegislation(legislation.id).unwrap();

      // Show result with protection stats
      const message = hasRules
        ? `Created: ${result.created_count} new rules\n` +
          `Deleted: ${result.deleted_count} unapproved rules\n` +
          `Protected: ${result.protected_count} approved/edited rules preserved`
        : `Created: ${result.created_count} rules`;

      showAlert({
        type: 'success',
        title: hasRules ? 'Re-digest Complete' : 'Digest Complete',
        message,
      });

      setShowRules(true);
    } catch (error: any) {
      console.error('Failed to digest legislation:', error);
      showAlert({
        type: 'error',
        title: 'Digest Failed',
        message: error.data?.detail || error.message || 'Unknown error occurred',
      });
    }
  };

  return (
    <Modal isOpen={true} onClose={onClose} title={legislation.statute_number} size="large">
      <>
        <div className={styles.field}>
          <label>Title</label>
          <p>{legislation.title}</p>
        </div>

        <div className={styles.field}>
          <label>Full Statutory Text</label>
          <pre className={styles.fullText}>{legislation.full_text}</pre>
        </div>

        {legislation.source_url && (
          <div className={styles.field}>
            <label>Source URL</label>
            <a
              href={legislation.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.link}
            >
              {legislation.source_url}
            </a>
          </div>
        )}

        {legislation.applies_to_page_types && (
          <div className={styles.field}>
            <label>Applies To</label>
            <p>{legislation.applies_to_page_types}</p>
          </div>
        )}

        <div className={styles.field}>
          <div className={styles.rulesHeader}>
            <label>Compliance Rules</label>
            <div className={styles.rulesActions}>
              <button
                onClick={() => setShowRules(!showRules)}
                className={styles.secondaryButton}
              >
                {showRules ? 'Hide Rules' : 'View Rules'}
              </button>
              <button
                onClick={handleReDigest}
                className={styles.digestButton}
                disabled={isDigesting}
              >
                {isDigesting
                  ? (rules.length === 0 ? 'Digesting...' : 'Re-digesting...')
                  : (rules.length === 0 ? 'Digest' : 'Re-digest')}
              </button>
            </div>
          </div>

          {showRules && (
            <div className={styles.rulesSection}>
              {rulesLoading ? (
                <div className={styles.loading}>Loading rules...</div>
              ) : rules.length === 0 ? (
                <div className={styles.emptyRules}>
                  <p>No rules have been generated from this legislation source yet.</p>
                  <p className={styles.helpText}>
                    Click "Re-digest" to generate compliance rules from this legislation.
                  </p>
                </div>
              ) : (
                <div className={styles.rulesList}>
                  {rules.map((rule) => (
                    <div
                      key={rule.id}
                      className={`${styles.ruleCard} ${
                        !rule.approved ? styles.unapproved : ''
                      }`}
                    >
                      <div className={styles.ruleHeader}>
                        <div className={styles.ruleBadges}>
                          {!rule.active && (
                            <span className={styles.inactiveBadge}>Inactive</span>
                          )}
                          {!rule.approved && (
                            <span className={styles.unapprovedBadge}>Not Approved</span>
                          )}
                        </div>
                      </div>
                      <div className={styles.ruleText}>{rule.rule_text}</div>
                      {rule.applies_to_page_types && (
                        <div className={styles.rulePageTypes}>
                          Applies to: {rule.applies_to_page_types}
                        </div>
                      )}
                    </div>
                  ))}
                  <div className={styles.rulesCount}>
                    {rules.length} rule{rules.length !== 1 ? 's' : ''} generated
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className={styles.metadata}>
          <div className={styles.metadataItem}>
            <span className={styles.metadataLabel}>State:</span>
            <span className={styles.metadataValue}>{legislation.state_code}</span>
          </div>
          {legislation.effective_date && (
            <div className={styles.metadataItem}>
              <span className={styles.metadataLabel}>Effective Date:</span>
              <span className={styles.metadataValue}>
                {new Date(legislation.effective_date).toLocaleDateString()}
              </span>
            </div>
          )}
          {legislation.sunset_date && (
            <div className={styles.metadataItem}>
              <span className={styles.metadataLabel}>Sunset Date:</span>
              <span className={styles.metadataValue}>
                {new Date(legislation.sunset_date).toLocaleDateString()}
              </span>
            </div>
          )}
          <div className={styles.metadataItem}>
            <span className={styles.metadataLabel}>Created:</span>
            <span className={styles.metadataValue}>
              {new Date(legislation.created_at).toLocaleString()}
            </span>
          </div>
        </div>
      </>
    </Modal>
  );
}
