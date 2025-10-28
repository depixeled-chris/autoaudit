import React, { useState } from 'react';
import {
  useGetLLMLogsQuery,
  useGetLLMStatsQuery,
  useGetAvailableModelsQuery,
  useGetModelConfigsQuery,
  useUpdateModelConfigMutation,
} from '../../../services/api/llmApi';
import styles from './LLMTab.module.scss';

export const LLMTab: React.FC = () => {
  const [selectedLog, setSelectedLog] = useState<number | null>(null);
  const [logLimit] = useState(50);
  const [logOffset] = useState(0);

  // Fetch data
  const { data: logsData, isLoading: logsLoading } = useGetLLMLogsQuery({
    limit: logLimit,
    offset: logOffset,
  });
  const { data: statsData, isLoading: statsLoading } = useGetLLMStatsQuery();
  const { data: availableModels, isLoading: modelsLoading } = useGetAvailableModelsQuery();
  const { data: configsData, isLoading: configsLoading, error: configsError } = useGetModelConfigsQuery();
  const [updateModelConfig] = useUpdateModelConfigMutation();

  // Debug logging
  if (configsError) {
    console.error('Model configs error:', configsError);
  }

  const handleModelChange = async (operation_type: string, model: string) => {
    try {
      await updateModelConfig({ operation_type, model }).unwrap();
    } catch (error) {
      console.error('Failed to update model:', error);
      alert('Failed to update model configuration');
    }
  };

  if (logsLoading || statsLoading || modelsLoading || configsLoading) {
    return <div className={styles.loading}>Loading LLM data...</div>;
  }

  return (
    <>
      {/* Stats Dashboard */}
      <section className={styles.statsSection}>
        <h3>Usage Statistics</h3>
        {statsData ? (
          <div className={styles.statsGrid}>
            <div className={styles.statCard}>
              <div className={styles.statLabel}>Total Calls</div>
              <div className={styles.statValue}>{(statsData.total_calls || 0).toLocaleString()}</div>
            </div>
            <div className={styles.statCard}>
              <div className={styles.statLabel}>Total Tokens</div>
              <div className={styles.statValue}>{(statsData.total_tokens || 0).toLocaleString()}</div>
            </div>
            <div className={styles.statCard}>
              <div className={styles.statLabel}>Total Cost</div>
              <div className={styles.statValue}>${(statsData.total_cost_usd || 0).toFixed(4)}</div>
            </div>
            <div className={styles.statCard}>
              <div className={styles.statLabel}>Avg Duration</div>
              <div className={styles.statValue}>{statsData.avg_duration_ms || 0}ms</div>
            </div>
          </div>
        ) : (
          <p>No usage data available yet.</p>
        )}

        {/* By Operation Type */}
        {statsData && statsData.by_operation && statsData.by_operation.length > 0 && (
          <div className={styles.breakdown}>
            <h4>By Operation Type</h4>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Operation</th>
                  <th>Calls</th>
                  <th>Tokens</th>
                  <th>Cost</th>
                </tr>
              </thead>
              <tbody>
                {statsData.by_operation.map((op) => (
                  <tr key={op.operation_type}>
                    <td>{op.operation_type}</td>
                    <td>{op.calls}</td>
                    <td>{op.tokens.toLocaleString()}</td>
                    <td>${op.cost_usd.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* By Model */}
        {statsData && statsData.by_model && statsData.by_model.length > 0 && (
          <div className={styles.breakdown}>
            <h4>By Model</h4>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Calls</th>
                  <th>Tokens</th>
                  <th>Cost</th>
                </tr>
              </thead>
              <tbody>
                {statsData.by_model.map((model) => (
                  <tr key={model.model}>
                    <td>{model.model}</td>
                    <td>{model.calls}</td>
                    <td>{model.tokens.toLocaleString()}</td>
                    <td>${model.cost_usd.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Model Configuration */}
      <section className={styles.configSection}>
        <h3>Model Configuration</h3>
        <p className={styles.description}>
          Configure which model to use for each operation type. Changes take effect immediately.
        </p>
        {configsLoading ? (
          <div className={styles.loading}>Loading model configurations...</div>
        ) : configsData?.configs && configsData.configs.length > 0 ? (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Operation Type</th>
                <th>Model</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {configsData.configs.map((config) => (
                <tr key={config.operation_type}>
                  <td><code>{config.operation_type}</code></td>
                  <td>
                    <select
                      value={config.model}
                      onChange={(e) => handleModelChange(config.operation_type, e.target.value)}
                      className={styles.modelSelect}
                    >
                      {availableModels?.map((model) => (
                        <option key={model} value={model}>
                          {model}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>{config.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div>
            <p>No model configurations found.</p>
            {configsError && (
              <pre style={{color: 'red', fontSize: '12px'}}>
                Error: {JSON.stringify(configsError, null, 2)}
              </pre>
            )}
          </div>
        )}
      </section>

      {/* Query History */}
      <section className={styles.logsSection}>
        <h3>Query History</h3>
        {logsData && (
          <>
            <div className={styles.logsHeader}>
              <span>{logsData.total} total queries</span>
              <span className={styles.totalCost}>
                Total cost: ${logsData.total_cost_usd.toFixed(4)}
              </span>
            </div>
            <div className={styles.tableContainer}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Operation</th>
                    <th>Model</th>
                    <th>Tokens</th>
                    <th>Cost</th>
                    <th>Duration</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {logsData.logs.map((log) => (
                    <tr
                      key={log.id}
                      className={selectedLog === log.id ? styles.selected : ''}
                      onClick={() => setSelectedLog(selectedLog === log.id ? null : log.id)}
                    >
                      <td>{new Date(log.created_at).toLocaleString()}</td>
                      <td><code>{log.operation_type}</code></td>
                      <td>{log.model}</td>
                      <td>{log.total_tokens.toLocaleString()}</td>
                      <td>${(log.total_cost_usd || 0).toFixed(4)}</td>
                      <td>{log.duration_ms}ms</td>
                      <td>
                        <span className={`${styles.status} ${styles[log.status]}`}>
                          {log.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Log Detail View */}
            {selectedLog && (
              <div className={styles.logDetail}>
                {logsData.logs.find((l) => l.id === selectedLog) && (
                  <div className={styles.logDetailContent}>
                    <h4>Query Details (ID: {selectedLog})</h4>
                    {(() => {
                      const log = logsData.logs.find((l) => l.id === selectedLog)!;
                      return (
                        <>
                          <div className={styles.detailSection}>
                            <strong>API Endpoint:</strong> {log.api_endpoint}
                          </div>
                          <div className={styles.detailSection}>
                            <strong>Input ({log.input_tokens} tokens):</strong>
                            <pre className={styles.codeBlock}>{log.input_text}</pre>
                          </div>
                          <div className={styles.detailSection}>
                            <strong>Output ({log.output_tokens} tokens):</strong>
                            <pre className={styles.codeBlock}>{log.output_text}</pre>
                          </div>
                          {log.error_message && (
                            <div className={styles.detailSection}>
                              <strong>Error:</strong>
                              <pre className={styles.errorBlock}>{log.error_message}</pre>
                            </div>
                          )}
                        </>
                      );
                    })()}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </section>
    </>
  );
};
