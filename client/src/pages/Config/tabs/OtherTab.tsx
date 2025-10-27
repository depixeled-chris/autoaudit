import { useState } from 'react';
import apiClient from '@lib/api/axios';
import { useAlert } from '@contexts/AlertContext';
import styles from './OtherTab.module.scss';

export default function OtherTab() {
  const [loading, setLoading] = useState<string | null>(null);
  const [results, setResults] = useState<{ type: string; message: string; details?: any } | null>(null);
  const { showConfirm } = useAlert();

  const handleClear = async (endpoint: string, confirmMessage: string, type: string) => {
    const confirmed = await showConfirm({
      title: 'Confirm Clear',
      message: confirmMessage,
      confirmText: 'Clear',
      variant: 'danger',
    });

    if (!confirmed) return;

    setLoading(type);
    setResults(null);

    try {
      const response = await apiClient.delete(`/api/demo/${endpoint}`);
      setResults({
        type: 'success',
        message: response.data.message,
        details: response.data,
      });
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Unknown error';
      setResults({
        type: 'error',
        message: `Failed: ${message}`,
      });
    } finally {
      setLoading(null);
    }
  };

  const handleNuclearReset = async () => {
    const confirmation1 = await showConfirm({
      title: '⚠️ NUCLEAR RESET ⚠️',
      message: 'This will DELETE ALL DATA except:\n- Your current user account\n- States list\n- Page types\n\nEverything else (projects, rules, preambles, legislation, other users) will be PERMANENTLY DELETED.\n\nAre you ABSOLUTELY SURE you want to continue?',
      confirmText: 'Yes, Continue',
      variant: 'danger',
    });

    if (!confirmation1) return;

    const confirmation2 = await showConfirm({
      title: '⚠️ FINAL WARNING ⚠️',
      message: 'This action CANNOT be undone.\n\nClick Confirm to proceed with the nuclear reset.',
      confirmText: 'RESET EVERYTHING',
      variant: 'danger',
    });

    if (!confirmation2) return;

    setLoading('nuclear');
    setResults(null);

    try {
      const response = await apiClient.delete('/api/demo/everything');
      setResults({
        type: 'success',
        message: response.data.message,
        details: response.data,
      });
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Unknown error';
      setResults({
        type: 'error',
        message: `Failed: ${message}`,
      });
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className={styles.otherTab}>
      <div className={styles.section}>
        <div className={styles.header}>
          <h2>Demo & Testing Utilities</h2>
          <p className={styles.subtitle}>
            Tools for clearing data during development and demos.
            <strong className={styles.warning}> These actions are destructive and cannot be undone.</strong>
          </p>
          <p className={styles.prodWarning}>
            ⚠️ <strong>Disabled in production</strong> for safety
          </p>
        </div>

        {results && (
          <div className={`${styles.results} ${styles[results.type]}`}>
            <p className={styles.message}>{results.message}</p>
            {results.details && (
              <pre className={styles.details}>{JSON.stringify(results.details, null, 2)}</pre>
            )}
          </div>
        )}

        <div className={styles.utilities}>
          <div className={styles.utilityCard}>
            <h3>Clear Rules</h3>
            <p>Delete all compliance rules extracted from legislation.</p>
            <button
              className={styles.dangerButton}
              onClick={() =>
                handleClear(
                  'rules',
                  'Are you sure you want to delete ALL rules? This cannot be undone.',
                  'rules'
                )
              }
              disabled={loading !== null}
            >
              {loading === 'rules' ? 'Deleting...' : 'Clear All Rules'}
            </button>
          </div>

          <div className={styles.utilityCard}>
            <h3>Clear Legislation</h3>
            <p>Delete all legislation sources and digests.</p>
            <button
              className={styles.dangerButton}
              onClick={() =>
                handleClear(
                  'legislation',
                  'Are you sure you want to delete ALL legislation sources? This cannot be undone.',
                  'legislation'
                )
              }
              disabled={loading !== null}
            >
              {loading === 'legislation' ? 'Deleting...' : 'Clear All Legislation'}
            </button>
          </div>

          <div className={styles.utilityCard}>
            <h3>Clear Preambles</h3>
            <p>Delete all preambles and their versions.</p>
            <button
              className={styles.dangerButton}
              onClick={() =>
                handleClear(
                  'preambles',
                  'Are you sure you want to delete ALL preambles? This cannot be undone.',
                  'preambles'
                )
              }
              disabled={loading !== null}
            >
              {loading === 'preambles' ? 'Deleting...' : 'Clear All Preambles'}
            </button>
          </div>

          <div className={styles.utilityCard}>
            <h3>Clear Projects</h3>
            <p>Delete all projects, URLs, and compliance checks.</p>
            <button
              className={styles.dangerButton}
              onClick={() =>
                handleClear(
                  'projects',
                  'Are you sure you want to delete ALL projects and checks? This cannot be undone.',
                  'projects'
                )
              }
              disabled={loading !== null}
            >
              {loading === 'projects' ? 'Deleting...' : 'Clear All Projects'}
            </button>
          </div>

          <div className={styles.utilityCard}>
            <h3>Clear Other Users</h3>
            <p>Delete all user accounts except your own.</p>
            <button
              className={styles.dangerButton}
              onClick={() =>
                handleClear(
                  'users',
                  'Are you sure you want to delete ALL other users? Your account will be kept. This cannot be undone.',
                  'users'
                )
              }
              disabled={loading !== null}
            >
              {loading === 'users' ? 'Deleting...' : 'Clear Other Users'}
            </button>
          </div>

          <div className={`${styles.utilityCard} ${styles.nuclear}`}>
            <h3>🔴 Nuclear Reset</h3>
            <p>
              <strong>DELETE EVERYTHING</strong> and reset to clean slate. Keeps only states, page
              types, and your user account.
            </p>
            <button
              className={styles.nuclearButton}
              onClick={handleNuclearReset}
              disabled={loading !== null}
            >
              {loading === 'nuclear' ? 'Resetting...' : '☢️ RESET EVERYTHING'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
