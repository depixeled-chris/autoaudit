import { useState } from 'react';
import {
  useGetStateByCodeQuery,
  useCreateStateMutation,
  useUpdateStateMutation,
  useGetLegislationSourcesQuery,
  useDeleteLegislationSourceMutation,
  type LegislationSource,
} from '@services/api/statesApi';
import { Modal } from '@components/ui/Modal/Modal';
import { Toggle } from '@components/ui/Toggle/Toggle';
import { useAlert } from '@contexts/AlertContext';
import AddLegislationModal from './AddLegislationModal';
import LegislationDetailsModal from './LegislationDetailsModal';
import styles from './StateConfigModal.module.scss';

interface Props {
  stateCode: string;
  onClose: () => void;
}

export default function StateConfigModal({ stateCode, onClose }: Props) {
  const [showAddLegislation, setShowAddLegislation] = useState(false);
  const [selectedLegislation, setSelectedLegislation] = useState<LegislationSource | null>(null);
  const { showAlert, showConfirm } = useAlert();

  const { data: stateData, isLoading: stateLoading, error: stateError } = useGetStateByCodeQuery(stateCode, { refetchOnMountOrArgChange: true });
  const { data: legislationData } = useGetLegislationSourcesQuery({ state_code: stateCode });
  const [createState] = useCreateStateMutation();
  const [updateState] = useUpdateStateMutation();
  const [deleteLegislationSource] = useDeleteLegislationSourceMutation();

  const state = stateData;
  const legislation = legislationData?.sources || [];
  // Debug logging
  console.log('StateConfigModal:', { stateCode, stateData, stateLoading, stateError, state });

  const handleToggleActive = async (newValue: boolean) => {
    try {
      if (state?.id) {
        // Update existing state
        await updateState({
          id: state.id,
          data: { active: newValue },
        }).unwrap();
      } else {
        // Create new state entry
        await createState({
          code: stateCode,
          name: getStateName(stateCode),
          active: newValue,
        }).unwrap();
      }
    } catch (error) {
      console.error('Failed to toggle state:', error);
    }
  };

  const handleDeleteLegislation = async (source: LegislationSource, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent opening the details modal

    const confirmed = await showConfirm({
      title: 'Delete Legislation',
      message: `Are you sure you want to delete "${source.statute_number}"?\n\nThis will permanently delete:\n- The legislation source\n- All associated digests\n- All generated compliance rules\n\nThis action cannot be undone.`,
      confirmText: 'Delete',
      variant: 'danger',
    });

    if (!confirmed) return;

    try {
      const result = await deleteLegislationSource(source.id).unwrap();
      console.log('Delete result:', result);
      showAlert({
        type: 'success',
        title: 'Legislation Deleted',
        message: `Successfully deleted ${result.statute_number}:\n- ${result.digests_deleted} digest(s)\n- ${result.rules_deleted} rule(s)`,
      });
    } catch (error: any) {
      console.error('Failed to delete legislation:', error);
      showAlert({
        type: 'error',
        title: 'Delete Failed',
        message: error.data?.error || error.message || 'Unknown error',
      });
    }
  };

  const getStateName = (code: string): string => {
    const stateNames: Record<string, string> = {
      AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California',
      CO: 'Colorado', CT: 'Connecticut', DE: 'Delaware', FL: 'Florida', GA: 'Georgia',
      HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois', IN: 'Indiana', IA: 'Iowa',
      KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland',
      MA: 'Massachusetts', MI: 'Michigan', MN: 'Minnesota', MS: 'Mississippi', MO: 'Missouri',
      MT: 'Montana', NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire', NJ: 'New Jersey',
      NM: 'New Mexico', NY: 'New York', NC: 'North Carolina', ND: 'North Dakota', OH: 'Ohio',
      OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island', SC: 'South Carolina',
      SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas', UT: 'Utah', VT: 'Vermont',
      VA: 'Virginia', WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming',
    };
    return stateNames[code] || code;
  };

  // If showing sub-modals, hide the main modal
  if (showAddLegislation) {
    return (
      <AddLegislationModal
        stateCode={stateCode}
        onClose={() => setShowAddLegislation(false)}
      />
    );
  }

  if (selectedLegislation) {
    return (
      <LegislationDetailsModal
        legislation={selectedLegislation}
        onClose={() => setSelectedLegislation(null)}
      />
    );
  }

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={`${stateCode} - ${getStateName(stateCode)}`}
      size="large"
    >
        <div className={styles.section}>
          <div className={styles.field}>
            <label className={styles.label}>State Status</label>
            <div className={styles.toggleRow}>
              <span className={styles.toggleLabel}>
                {state?.active ? 'Enabled' : 'Disabled'}
              </span>
              <Toggle
                checked={state?.active || false}
                onChange={handleToggleActive}
              />
            </div>
            <p className={styles.helpText}>
              {state?.active
                ? 'This state is enabled for compliance checking'
                : 'Enable this state to configure legislation and run compliance checks'}
            </p>
          </div>
        </div>

        <div className={styles.section}>
          <div className={styles.sectionHeader}>
            <div>
              <label className={styles.label}>Legislation Sources</label>
              <p className={styles.helpText}>
                Undoctored statutory text for this state
              </p>
            </div>
            <button
              className={styles.addButton}
              onClick={() => setShowAddLegislation(true)}
            >
              + Add Legislation
            </button>
          </div>

          {legislation.length === 0 ? (
            <div className={styles.emptyState}>
              <p>No legislation sources configured</p>
              <button
                className={styles.secondaryButton}
                onClick={() => setShowAddLegislation(true)}
              >
                Add First Legislation Source
              </button>
            </div>
          ) : (
            <div className={styles.legislationList}>
              {legislation.map((source) => (
                <div
                  key={source.id}
                  className={styles.legislationCard}
                  onClick={() => setSelectedLegislation(source)}
                >
                  <div className={styles.legislationHeader}>
                    <div>
                      <div className={styles.statuteNumber}>{source.statute_number}</div>
                      <div className={styles.title}>{source.title}</div>
                    </div>
                    <div className={styles.legislationActions}>
                      {source.effective_date && (
                        <div className={styles.date}>
                          Effective: {new Date(source.effective_date).toLocaleDateString()}
                        </div>
                      )}
                      <button
                        className={styles.deleteButton}
                        onClick={(e) => handleDeleteLegislation(source, e)}
                        title="Delete this legislation source and all associated rules"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  {source.applies_to_page_types && (
                    <div className={styles.pageTypes}>
                      Applies to: {source.applies_to_page_types}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </Modal>
  );
}
