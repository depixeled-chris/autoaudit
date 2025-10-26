import { useState } from 'react';
import { ExternalLink, RefreshCw, FileText, Trash2 } from 'lucide-react';
import { useGetURLsQuery, useDeleteURLMutation, useUpdateURLMutation, useForceRescanURLMutation, type MonitoredURL } from '../urlsApi';
import { useGetLatestCheckForUrlQuery } from '@features/checks/checksApi';
import { CheckDetailModal } from '@features/checks/components/CheckDetailModal';
import EditURLModal from './EditURLModal';
import { Button } from '@components/ui/Button';
import { Badge } from '@components/ui/Badge';
import { Toggle } from '@components/ui/Toggle';
import { ToastContainer } from '@components/ui/Toast';
import { useToast } from '@hooks/useToast';
import styles from './URLList.module.scss';

interface URLListProps {
  projectId: number;
}

interface URLCheckModalProps {
  urlId: number;
  url?: MonitoredURL;
  onClose: () => void;
  onRescan: (url: MonitoredURL) => void;
  isRescanning: boolean;
}

const URLCheckModal = ({ urlId, url, onClose, onRescan, isRescanning }: URLCheckModalProps) => {
  const { data: check, isLoading, error } = useGetLatestCheckForUrlQuery(urlId);

  // Show spinner if rescanning and no check data yet
  if (isRescanning && !check) {
    return (
      <div className={styles.modalOverlay}>
        <div className={styles.modalLoading}>
          <RefreshCw size={32} className={styles.spinning} />
          <p>Scanning in progress...</p>
          <p className={styles.modalLoadingSubtext}>This may take 30-60 seconds</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={styles.modalOverlay}>
        <div className={styles.modalLoading}>Loading check details...</div>
      </div>
    );
  }

  if (error || !check) {
    return (
      <div className={styles.modalOverlay} onClick={onClose}>
        <div className={styles.modalError} onClick={(e) => e.stopPropagation()}>
          <p>No check data available for this URL.</p>
          <Button onClick={onClose}>Close</Button>
        </div>
      </div>
    );
  }

  return (
    <CheckDetailModal
      check={check}
      isOpen={true}
      onClose={onClose}
      onRescan={url ? () => onRescan(url) : undefined}
      isRescanning={isRescanning}
    />
  );
};

export const URLList = ({ projectId }: URLListProps) => {
  const { data: urls, isLoading } = useGetURLsQuery({ project_id: projectId, active_only: false });
  const [deleteURL] = useDeleteURLMutation();
  const [updateURL] = useUpdateURLMutation();
  const [forceRescan] = useForceRescanURLMutation();
  const [rescanningId, setRescanningId] = useState<number | null>(null);
  const [selectedUrlId, setSelectedUrlId] = useState<number | null>(null);
  const [editingUrl, setEditingUrl] = useState<MonitoredURL | null>(null);
  const { toasts, removeToast, success, error, info } = useToast();

  const handleToggleActive = async (url: MonitoredURL) => {
    try {
      await updateURL({ id: url.id, data: { active: !url.active } }).unwrap();
    } catch (error) {
      console.error('Failed to toggle URL active status:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to deactivate this URL?')) {
      try {
        await deleteURL(id).unwrap();
      } catch (error) {
        console.error('Failed to delete URL:', error);
      }
    }
  };

  const handleViewDetails = (urlId: number, event: React.MouseEvent) => {
    event.stopPropagation();
    setSelectedUrlId(urlId);
  };

  const handleCloseModal = () => {
    setSelectedUrlId(null);
  };

  const handleSaveURL = async (id: number, data: Partial<MonitoredURL>) => {
    await updateURL({ id, data }).unwrap();
    success('URL settings updated successfully');
  };

  const handleForceRescan = async (id: number, url: MonitoredURL, event?: React.MouseEvent) => {
    if (event) {
      event.stopPropagation();
    }
    setRescanningId(id);

    const urlType = url.url_type.toLowerCase();
    const isInventory = urlType === 'inventory';

    // Show different messages based on scan type
    if (isInventory) {
      info('Scheduling batch scan for inventory URL...', 3000);
    } else {
      info('Starting compliance scan... This may take 30-60 seconds.', 3000);
    }

    try {
      const result: any = await forceRescan(id).unwrap();

      if (result.scan_type === 'batch') {
        success(
          `Batch scan scheduled. Results will be available within 24 hours.`,
          7000
        );
      } else if (result.scan_type === 'immediate') {
        // Determine status display
        let statusText = 'Unknown';
        let statusEmoji = '❓';

        if (result.compliance_status === 'COMPLIANT') {
          statusText = 'Compliant';
          statusEmoji = '✅';
        } else if (result.overall_score >= 80) {
          statusText = 'Mostly Compliant';
          statusEmoji = '✓';
        } else if (result.overall_score >= 60) {
          statusText = 'Needs Review';
          statusEmoji = '⚠️';
        } else {
          statusText = 'Non-Compliant';
          statusEmoji = '❌';
        }

        // Show detailed results
        success(
          `${statusEmoji} Scan Complete!\n` +
          `Status: ${statusText} | Score: ${result.overall_score}/100\n` +
          `${result.violations_count} violations found | Check ID: ${result.check_id}`,
          15000 // 15 seconds for user to read
        );

        // Log the check_id for now (until we have a detail view)
        console.log('Scan results:', result);
        console.log(`View detailed results: /api/checks/${result.check_id}`);
      }
    } catch (err: any) {
      console.error('Failed to force rescan:', err);
      const errorMessage = err?.data?.detail || 'Failed to start scan. Please try again.';
      error(errorMessage, 7000);
    } finally {
      setRescanningId(null);
    }
  };

  if (isLoading) {
    return <div className={styles.loading}>Loading URLs...</div>;
  }

  if (!urls || urls.length === 0) {
    return (
      <div className={styles.empty}>
        <p>No URLs added yet. Click "Add URL" to start monitoring compliance.</p>
      </div>
    );
  }

  // Get the selected URL data
  const selectedUrl = urls?.find(u => u.id === selectedUrlId);

  return (
    <>
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      {selectedUrlId && <URLCheckModal
        urlId={selectedUrlId}
        url={selectedUrl}
        onClose={handleCloseModal}
        onRescan={(url) => handleForceRescan(selectedUrlId, url)}
        isRescanning={rescanningId === selectedUrlId}
      />}
      <div className={styles.tableContainer}>
        <table className={styles.urlTable}>
          <thead>
            <tr>
              <th>URL</th>
              <th>Type</th>
              <th>Platform</th>
              <th>Scans</th>
              <th>Last Checked</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {urls.map((url) => (
              <tr
                key={url.id}
                className={!url.active ? styles.inactive : ''}
                onClick={() => setEditingUrl(url)}
                style={{ cursor: 'pointer' }}
              >
                <td className={styles.urlCell} onClick={(e) => e.stopPropagation()}>
                  <a
                    href={url.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={styles.urlLink}
                    title={url.url}
                  >
                    <ExternalLink size={14} />
                    <span className={styles.urlText}>{url.url}</span>
                  </a>
                </td>
                <td>
                  <Badge variant="secondary">{url.url_type}</Badge>
                </td>
                <td>
                  {url.platform ? (
                    <Badge variant="secondary">{url.platform}</Badge>
                  ) : (
                    <span className={styles.emptyCell}>—</span>
                  )}
                </td>
                <td className={styles.scanCount}>
                  {url.check_count}
                </td>
                <td className={styles.dateCell}>
                  {url.last_checked ? (
                    <span title={new Date(url.last_checked).toLocaleString()}>
                      {new Date(url.last_checked).toLocaleString()}
                    </span>
                  ) : (
                    <span className={styles.emptyCell}>Never</span>
                  )}
                </td>
                <td onClick={(e) => e.stopPropagation()}>
                  <Toggle
                    checked={url.active}
                    onChange={() => handleToggleActive(url)}
                    size="small"
                  />
                </td>
                <td className={styles.actionsCell} onClick={(e) => e.stopPropagation()}>
                  <div className={styles.actionButtons}>
                    <Button
                      variant="ghost"
                      size="small"
                      onClick={(e) => handleViewDetails(url.id, e)}
                      disabled={!url.last_checked}
                      title={url.last_checked ? "View scan details" : "No scans yet"}
                    >
                      <FileText size={16} />
                    </Button>
                    <Button
                      variant="ghost"
                      size="small"
                      onClick={(e) => handleForceRescan(url.id, url, e)}
                      disabled={rescanningId === url.id}
                      title="Rescan"
                    >
                      <RefreshCw size={16} className={rescanningId === url.id ? styles.spinning : ''} />
                    </Button>
                    <Button
                      variant="ghost"
                      size="small"
                      onClick={() => handleDelete(url.id)}
                      title="Remove"
                    >
                      <Trash2 size={16} />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editingUrl && (
        <EditURLModal
          url={editingUrl}
          isOpen={true}
          onClose={() => setEditingUrl(null)}
          onSave={handleSaveURL}
          onDelete={handleDelete}
        />
      )}
    </>
  );
};
