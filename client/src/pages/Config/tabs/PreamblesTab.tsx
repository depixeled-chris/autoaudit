import { useState } from 'react';
import {
  useGetPreamblesQuery,
  useGetPreambleVersionsQuery,
  useActivatePreambleVersionMutation,
  type Preamble,
} from '@services/api/preamblesApi';
import { useAlert } from '@contexts/AlertContext';
import styles from './PreamblesTab.module.scss';
import CreatePreambleModal from '../components/CreatePreambleModal';
import CreateVersionModal from '../components/CreateVersionModal';

export default function PreamblesTab() {
  const [selectedScope, setSelectedScope] = useState<string>('universal');
  const [selectedPreamble, setSelectedPreamble] = useState<Preamble | null>(null);
  const [showCreatePreamble, setShowCreatePreamble] = useState(false);
  const [showCreateVersion, setShowCreateVersion] = useState(false);
  const { showConfirm } = useAlert();

  const { data: preamblesData } = useGetPreamblesQuery({ scope: selectedScope });
  const { data: versionsData } = useGetPreambleVersionsQuery(selectedPreamble?.id || 0, {
    skip: !selectedPreamble,
  });
  const [activateVersion] = useActivatePreambleVersionMutation();

  const preambles = preamblesData?.preambles || [];
  const versions = versionsData?.versions || [];

  const handleActivateVersion = async (versionId: number) => {
    const confirmed = await showConfirm({
      title: 'Activate Version',
      message: 'Activate this version? This will retire the current active version and invalidate caches.',
      confirmText: 'Activate',
      variant: 'warning',
    });

    if (!confirmed) return;

    try {
      await activateVersion(versionId).unwrap();
    } catch (error) {
      console.error('Failed to activate:', error);
    }
  };

  return (
    <div className={styles.preamblesTab}>
      <div className={styles.sidebar}>
        <div className={styles.sidebarHeader}>
          <h3>Scope</h3>
          <button className={styles.addButton} onClick={() => setShowCreatePreamble(true)}>
            + New
          </button>
        </div>
        <div className={styles.scopeButtons}>
          {['universal', 'state', 'page_type', 'project'].map((scope) => (
            <button
              key={scope}
              className={selectedScope === scope ? styles.active : ''}
              onClick={() => setSelectedScope(scope)}
            >
              {scope.replace('_', ' ')}
            </button>
          ))}
        </div>

        <div className={styles.preamblesList}>
          {preambles.map((preamble) => (
            <div
              key={preamble.id}
              className={`${styles.preambleItem} ${
                selectedPreamble?.id === preamble.id ? styles.selected : ''
              }`}
              onClick={() => setSelectedPreamble(preamble)}
            >
              <div className={styles.preambleName}>{preamble.name}</div>
              <div className={styles.machineName}>{preamble.machine_name}</div>
              {preamble.active_version && (
                <div className={styles.version}>v{preamble.active_version.version_number}</div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className={styles.main}>
        {selectedPreamble ? (
          <>
            <div className={styles.preambleHeader}>
              <div>
                <h2>{selectedPreamble.name}</h2>
                <p className={styles.subtitle}>{selectedPreamble.machine_name}</p>
              </div>
              <button
                className={styles.primaryButton}
                onClick={() => setShowCreateVersion(true)}
              >
                + New Version
              </button>
            </div>

            {selectedPreamble.active_version && (
              <div className={styles.activeVersion}>
                <h3>Active Version {selectedPreamble.active_version.version_number}</h3>
                <pre className={styles.preambleText}>
                  {selectedPreamble.active_version.preamble_text}
                </pre>
              </div>
            )}

            <div className={styles.versionsSection}>
              <h3>All Versions</h3>
              <div className={styles.versionsList}>
                {versions.map((version) => (
                  <div
                    key={version.id}
                    className={`${styles.versionCard} ${
                      version.status === 'active' ? styles.active : ''
                    }`}
                  >
                    <div className={styles.versionHeader}>
                      <div>
                        <span className={styles.versionNumber}>v{version.version_number}</span>
                        <span className={styles.status}>{version.status}</span>
                      </div>
                      {version.status !== 'active' && (
                        <button
                          className={styles.activateButton}
                          onClick={() => handleActivateVersion(version.id)}
                        >
                          Activate
                        </button>
                      )}
                    </div>
                    {version.change_summary && (
                      <div className={styles.changeSummary}>{version.change_summary}</div>
                    )}
                    <div className={styles.versionDate}>
                      {new Date(version.created_at).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        ) : (
          <div className={styles.emptyState}>
            <p>Select a preamble to view versions</p>
          </div>
        )}
      </div>

      {showCreatePreamble && (
        <CreatePreambleModal onClose={() => setShowCreatePreamble(false)} />
      )}
      {showCreateVersion && selectedPreamble && (
        <CreateVersionModal
          preambleId={selectedPreamble.id}
          onClose={() => setShowCreateVersion(false)}
        />
      )}
    </div>
  );
}
