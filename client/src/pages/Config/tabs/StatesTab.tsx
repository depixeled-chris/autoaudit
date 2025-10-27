import { useState } from 'react';
import {
  useGetStatesQuery,
  useCreateStateMutation,
  useUpdateStateMutation,
  type State,
} from '@services/api/statesApi';
import { Toggle } from '@components/ui/Toggle/Toggle';
import styles from './StatesTab.module.scss';
import StateConfigModal from '../components/StateConfigModal';

// All 50 US states
const ALL_US_STATES = [
  { code: 'AL', name: 'Alabama' },
  { code: 'AK', name: 'Alaska' },
  { code: 'AZ', name: 'Arizona' },
  { code: 'AR', name: 'Arkansas' },
  { code: 'CA', name: 'California' },
  { code: 'CO', name: 'Colorado' },
  { code: 'CT', name: 'Connecticut' },
  { code: 'DE', name: 'Delaware' },
  { code: 'FL', name: 'Florida' },
  { code: 'GA', name: 'Georgia' },
  { code: 'HI', name: 'Hawaii' },
  { code: 'ID', name: 'Idaho' },
  { code: 'IL', name: 'Illinois' },
  { code: 'IN', name: 'Indiana' },
  { code: 'IA', name: 'Iowa' },
  { code: 'KS', name: 'Kansas' },
  { code: 'KY', name: 'Kentucky' },
  { code: 'LA', name: 'Louisiana' },
  { code: 'ME', name: 'Maine' },
  { code: 'MD', name: 'Maryland' },
  { code: 'MA', name: 'Massachusetts' },
  { code: 'MI', name: 'Michigan' },
  { code: 'MN', name: 'Minnesota' },
  { code: 'MS', name: 'Mississippi' },
  { code: 'MO', name: 'Missouri' },
  { code: 'MT', name: 'Montana' },
  { code: 'NE', name: 'Nebraska' },
  { code: 'NV', name: 'Nevada' },
  { code: 'NH', name: 'New Hampshire' },
  { code: 'NJ', name: 'New Jersey' },
  { code: 'NM', name: 'New Mexico' },
  { code: 'NY', name: 'New York' },
  { code: 'NC', name: 'North Carolina' },
  { code: 'ND', name: 'North Dakota' },
  { code: 'OH', name: 'Ohio' },
  { code: 'OK', name: 'Oklahoma' },
  { code: 'OR', name: 'Oregon' },
  { code: 'PA', name: 'Pennsylvania' },
  { code: 'RI', name: 'Rhode Island' },
  { code: 'SC', name: 'South Carolina' },
  { code: 'SD', name: 'South Dakota' },
  { code: 'TN', name: 'Tennessee' },
  { code: 'TX', name: 'Texas' },
  { code: 'UT', name: 'Utah' },
  { code: 'VT', name: 'Vermont' },
  { code: 'VA', name: 'Virginia' },
  { code: 'WA', name: 'Washington' },
  { code: 'WV', name: 'West Virginia' },
  { code: 'WI', name: 'Wisconsin' },
  { code: 'WY', name: 'Wyoming' },
];

export default function StatesTab() {
  const [selectedStateCode, setSelectedStateCode] = useState<string | null>(null);
  const [showActiveOnly, setShowActiveOnly] = useState(true);

  const { data: statesData, isLoading: statesLoading } = useGetStatesQuery({ active_only: false });
  const [createState] = useCreateStateMutation();
  const [updateState] = useUpdateStateMutation();

  const dbStates = statesData?.states || [];

  // Create a map of database states for quick lookup
  const dbStatesMap = new Map(dbStates.map(s => [s.code, s]));

  // Merge all US states with database state info
  const allStates = ALL_US_STATES.map(usState => {
    const dbState = dbStatesMap.get(usState.code);
    return {
      code: usState.code,
      name: usState.name,
      id: dbState?.id,
      active: dbState?.active || false,
      legislationCount: 0, // We'll need to fetch this separately if needed
    };
  });

  // Filter states based on toggle
  const filteredStates = showActiveOnly
    ? allStates.filter(state => state.active)
    : allStates;

  const handleToggleState = async (state: typeof allStates[0], newValue: boolean) => {
    try {
      if (state.id) {
        // Update existing state
        await updateState({
          id: state.id,
          data: { active: newValue },
        }).unwrap();
      } else {
        // Create new state entry
        await createState({
          code: state.code,
          name: state.name,
          active: newValue,
        }).unwrap();
      }
    } catch (error) {
      console.error('Failed to toggle state:', error);
    }
  };

  return (
    <div className={styles.statesTab}>
      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <div>
            <h2>States Configuration</h2>
            <p>Configure legislation and compliance settings for each state</p>
          </div>
          <div className={styles.filterRow}>
            <label className={styles.filterLabel}>Show enabled only</label>
            <Toggle
              checked={showActiveOnly}
              onChange={setShowActiveOnly}
              size="small"
            />
          </div>
        </div>

        {statesLoading ? (
          <div className={styles.loading}>Loading states...</div>
        ) : (
          <div className={styles.tableContainer}>
            <table className={styles.statesTable}>
              <thead>
                <tr>
                  <th>State</th>
                  <th>Code</th>
                  <th>Enabled</th>
                  <th>Legislation</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredStates.map((state) => (
                  <tr key={state.code} className={!state.active ? styles.disabled : ''}>
                    <td className={styles.stateName}>{state.name}</td>
                    <td className={styles.stateCode}>{state.code}</td>
                    <td>
                      <Toggle
                        checked={state.active}
                        onChange={(newValue) => handleToggleState(state, newValue)}
                        size="small"
                      />
                    </td>
                    <td className={styles.legislationCount}>
                      {state.legislationCount > 0 ? `${state.legislationCount} sources` : '—'}
                    </td>
                    <td>
                      <button
                        className={styles.configButton}
                        onClick={() => setSelectedStateCode(state.code)}
                      >
                        Configure
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedStateCode && (
        <StateConfigModal
          stateCode={selectedStateCode}
          onClose={() => setSelectedStateCode(null)}
        />
      )}
    </div>
  );
}
