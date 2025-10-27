import { useState } from 'react';
import {
  useGetRulesQuery,
  useUpdateRuleMutation,
  useDeleteRuleMutation,
  useDeleteStateRulesMutation,
  useDigestLegislationMutation,
  type Rule,
} from '@services/api/rulesApi';
import { useGetStatesQuery } from '@services/api/statesApi';
import { Toggle } from '@components/ui/Toggle/Toggle';
import { useAlert } from '@contexts/AlertContext';
import RuleDetailModal from '../components/RuleDetailModal';
import styles from './RulesTab.module.scss';

export default function RulesTab() {
  const [selectedStateCode, setSelectedStateCode] = useState<string>('');
  const [showActiveOnly, setShowActiveOnly] = useState(false);
  const [showApprovedOnly, setShowApprovedOnly] = useState(false);
  const [selectedRule, setSelectedRule] = useState<Rule | null>(null);
  const [expandedRules, setExpandedRules] = useState<Set<number>>(new Set());
  const { showAlert, showConfirm } = useAlert();

  const { data: statesData } = useGetStatesQuery({ active_only: false });
  const { data: rulesData, isLoading: rulesLoading } = useGetRulesQuery({
    state_code: selectedStateCode || undefined,
    active_only: showActiveOnly,
    approved_only: showApprovedOnly,
  });

  const [updateRule] = useUpdateRuleMutation();
  const [deleteRule] = useDeleteRuleMutation();
  const [deleteStateRules] = useDeleteStateRulesMutation();
  const [digestLegislation, { isLoading: isDigesting }] = useDigestLegislationMutation();

  const states = statesData?.states || [];
  const rules = rulesData?.rules || [];

  const handleToggleActive = async (rule: Rule) => {
    try {
      await updateRule({
        id: rule.id,
        data: { active: !rule.active },
      }).unwrap();
    } catch (error) {
      console.error('Failed to toggle rule active status:', error);
    }
  };

  const handleToggleApproved = async (rule: Rule) => {
    try {
      await updateRule({
        id: rule.id,
        data: { approved: !rule.approved },
      }).unwrap();
    } catch (error) {
      console.error('Failed to toggle rule approval:', error);
    }
  };

  const handleDeleteRule = async (ruleId: number) => {
    const confirmed = await showConfirm({
      title: 'Delete Rule',
      message: 'Are you sure you want to delete this rule? This action cannot be undone.',
      confirmText: 'Delete',
      variant: 'danger',
    });

    if (!confirmed) return;

    try {
      await deleteRule(ruleId).unwrap();
    } catch (error) {
      console.error('Failed to delete rule:', error);
    }
  };

  const handleReDigestState = async () => {
    if (!selectedStateCode) {
      showAlert({
        type: 'warning',
        title: 'No State Selected',
        message: 'Please select a state first.',
      });
      return;
    }

    const confirmed = await showConfirm({
      title: 'Re-digest All Rules',
      message: `This will delete all existing rules for ${selectedStateCode} and regenerate them from legislation sources. This action cannot be undone. Continue?`,
      confirmText: 'Re-digest All',
      variant: 'danger',
    });

    if (!confirmed) return;

    try {
      await digestLegislation({ state_code: selectedStateCode }).unwrap();
      showAlert({
        type: 'success',
        title: 'Re-digest Complete',
        message: 'Rules have been regenerated successfully!',
      });
    } catch (error: any) {
      console.error('Failed to re-digest legislation:', error);
      showAlert({
        type: 'error',
        title: 'Re-digest Failed',
        message: error.data?.detail || error.message || 'Unknown error',
      });
    }
  };

  const toggleExpand = (ruleId: number) => {
    const newExpanded = new Set(expandedRules);
    if (newExpanded.has(ruleId)) {
      newExpanded.delete(ruleId);
    } else {
      newExpanded.add(ruleId);
    }
    setExpandedRules(newExpanded);
  };

  const truncateText = (text: string, maxLength: number = 150) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <div className={styles.rulesTab}>
      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <div>
            <h2>Compliance Rules</h2>
            <p>Manage atomic compliance requirements extracted from legislation</p>
          </div>
        </div>

        <div className={styles.filterControls}>
          <div className={styles.filterRow}>
            <label className={styles.filterLabel}>State</label>
            <select
              className={styles.stateSelect}
              value={selectedStateCode}
              onChange={(e) => setSelectedStateCode(e.target.value)}
            >
              <option value="">All States</option>
              {states.map((state) => (
                <option key={state.code} value={state.code}>
                  {state.code} - {state.name}
                </option>
              ))}
            </select>
          </div>

          <div className={styles.filterRow}>
            <label className={styles.filterLabel}>Show active only</label>
            <Toggle checked={showActiveOnly} onChange={setShowActiveOnly} size="small" />
          </div>

          <div className={styles.filterRow}>
            <label className={styles.filterLabel}>Show approved only</label>
            <Toggle checked={showApprovedOnly} onChange={setShowApprovedOnly} size="small" />
          </div>

          {selectedStateCode && (
            <button
              className={styles.digestButton}
              onClick={handleReDigestState}
              disabled={isDigesting}
            >
              {isDigesting ? 'Re-digesting...' : 'Re-digest All'}
            </button>
          )}
        </div>

        {rulesLoading ? (
          <div className={styles.loading}>Loading rules...</div>
        ) : rules.length === 0 ? (
          <div className={styles.empty}>
            <p>
              {selectedStateCode
                ? `No rules found for ${selectedStateCode}`
                : 'No rules found. Select a state and add legislation sources to generate rules.'}
            </p>
          </div>
        ) : (
          <div className={styles.tableContainer}>
            <table className={styles.rulesTable}>
              <thead>
                <tr>
                  <th>State</th>
                  <th>Digest</th>
                  <th>Rule Text</th>
                  <th>Page Types</th>
                  <th>Flags</th>
                  <th>Active</th>
                  <th>Approved</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((rule) => {
                  const isExpanded = expandedRules.has(rule.id);
                  const displayText = isExpanded
                    ? rule.rule_text
                    : truncateText(rule.rule_text);

                  return (
                    <tr
                      key={rule.id}
                      className={!rule.active ? styles.disabled : !rule.approved ? styles.unapproved : ''}
                    >
                      <td className={styles.stateCode}>{rule.state_code}</td>
                      <td className={styles.digestId}>
                        {rule.legislation_digest_id ? (
                          <span className={styles.digestBadge} title={`Digest ID: ${rule.legislation_digest_id}`}>
                            #{rule.legislation_digest_id}
                          </span>
                        ) : (
                          <span className={styles.noDigest} title="Created before digest versioning">—</span>
                        )}
                      </td>
                      <td className={styles.ruleText}>
                        <div>
                          {displayText}
                          {rule.rule_text.length > 150 && (
                            <button
                              className={styles.expandButton}
                              onClick={() => toggleExpand(rule.id)}
                            >
                              {isExpanded ? 'Show less' : 'Show more'}
                            </button>
                          )}
                        </div>
                      </td>
                      <td className={styles.pageTypes}>
                        {rule.applies_to_page_types || '—'}
                      </td>
                      <td className={styles.flagsCell}>
                        {rule.is_manually_modified && (
                          <span className={styles.modifiedBadge} title="Manually edited">
                            ✏️
                          </span>
                        )}
                        {rule.status !== 'active' && (
                          <span className={styles.statusBadge} title={`Status: ${rule.status}`}>
                            {rule.status}
                          </span>
                        )}
                      </td>
                      <td>
                        <Toggle
                          checked={rule.active}
                          onChange={() => handleToggleActive(rule)}
                          size="small"
                        />
                      </td>
                      <td>
                        <input
                          type="checkbox"
                          checked={rule.approved}
                          onChange={() => handleToggleApproved(rule)}
                          className={styles.checkbox}
                        />
                      </td>
                      <td className={styles.actions}>
                        <button
                          className={styles.editButton}
                          onClick={() => setSelectedRule(rule)}
                        >
                          Edit
                        </button>
                        <button
                          className={styles.deleteButton}
                          onClick={() => handleDeleteRule(rule.id)}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {rules.length > 0 && (
          <div className={styles.tableFooter}>
            <p className={styles.resultCount}>
              Showing {rules.length} rule{rules.length !== 1 ? 's' : ''}
            </p>
          </div>
        )}
      </div>

      {selectedRule && (
        <RuleDetailModal rule={selectedRule} onClose={() => setSelectedRule(null)} />
      )}
    </div>
  );
}
