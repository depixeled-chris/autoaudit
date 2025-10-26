import { RefreshCw, CheckCircle, AlertTriangle, XCircle, FileText, Eye, Download } from 'lucide-react';
import type { Check } from '../checksApi';
import { Modal } from '@components/ui/Modal/Modal';
import { Button } from '@components/ui/Button';
import { Badge } from '@components/ui/Badge';
import styles from './CheckDetailModal.module.scss';

interface CheckDetailModalProps {
  check: Check;
  isOpen: boolean;
  onClose: () => void;
  onRescan?: () => void;
  isRescanning?: boolean;
}

export const CheckDetailModal = ({
  check,
  isOpen,
  onClose,
  onRescan,
  isRescanning = false,
}: CheckDetailModalProps) => {
  // Determine status display
  const getStatusInfo = () => {
    const status = check.compliance_status.toLowerCase();
    const score = check.overall_score;

    if (status === 'compliant' || score >= 90) {
      return {
        icon: <CheckCircle size={24} />,
        text: 'Compliant',
        variant: 'success' as const,
        emoji: '✅',
      };
    } else if (score >= 80) {
      return {
        icon: <CheckCircle size={24} />,
        text: 'Mostly Compliant',
        variant: 'success' as const,
        emoji: '✓',
      };
    } else if (score >= 60) {
      return {
        icon: <AlertTriangle size={24} />,
        text: 'Needs Review',
        variant: 'warning' as const,
        emoji: '⚠️',
      };
    } else {
      return {
        icon: <XCircle size={24} />,
        text: 'Non-Compliant',
        variant: 'danger' as const,
        emoji: '❌',
      };
    }
  };

  const statusInfo = getStatusInfo();

  // Group violations by severity
  const violationsBySeverity = {
    high: check.violations?.filter(v => v.severity.toLowerCase() === 'high') || [],
    medium: check.violations?.filter(v => v.severity.toLowerCase() === 'medium') || [],
    low: check.violations?.filter(v => v.severity.toLowerCase() === 'low') || [],
  };

  const getSeverityVariant = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high':
        return 'danger';
      case 'medium':
        return 'warning';
      case 'low':
        return 'secondary';
      default:
        return 'secondary';
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="large" showCloseButton={false}>
      <div className={styles.modalContent}>
        {isRescanning && (
          <div className={styles.rescanBanner}>
            <RefreshCw size={16} className={styles.spinning} />
            <span>Rescanning in progress... Showing previous results</span>
          </div>
        )}

        <div className={styles.headerSection}>
          <div>
            <h2>Compliance Check Details</h2>
            <p className={styles.url}>{check.url}</p>
          </div>
        </div>

        <div className={styles.body}>
          {/* Score and Status Section */}
          <div className={styles.scoreSection}>
            <div className={styles.scoreCard}>
              <div className={styles.scoreValue}>{check.overall_score}</div>
              <div className={styles.scoreLabel}>Compliance Score</div>
            </div>
            <div className={styles.statusCard}>
              <div className={`${styles.statusIcon} ${styles[statusInfo.variant]}`}>
                {statusInfo.icon}
              </div>
              <div>
                <div className={styles.statusText}>{statusInfo.text}</div>
                <div className={styles.statusDate}>
                  Checked: {new Date(check.checked_at).toLocaleString()}
                </div>
              </div>
            </div>
          </div>

          {/* Summary */}
          {check.summary && (
            <div className={styles.section}>
              <h3>Summary</h3>
              <p className={styles.summary}>{check.summary}</p>
            </div>
          )}

          {/* Violations */}
          {check.violations && check.violations.length > 0 ? (
            <div className={styles.section}>
              <h3>Violations ({check.violations.length})</h3>

              {violationsBySeverity.high.length > 0 && (
                <div className={styles.violationGroup}>
                  <h4 className={styles.severityHeader}>
                    <Badge variant="danger">High Severity</Badge>
                    <span className={styles.count}>({violationsBySeverity.high.length})</span>
                  </h4>
                  {violationsBySeverity.high.map((violation) => (
                    <div key={violation.id} className={styles.violation}>
                      <div className={styles.violationHeader}>
                        <span className={styles.category}>{violation.category}</span>
                        {violation.confidence && (
                          <span className={styles.confidence}>
                            Confidence: {Math.round(violation.confidence * 100)}%
                          </span>
                        )}
                      </div>
                      <div className={styles.ruleViolated}>{violation.rule_violated}</div>
                      {violation.explanation && (
                        <p className={styles.explanation}>{violation.explanation}</p>
                      )}
                      {violation.evidence && (
                        <div className={styles.evidence}>
                          <strong>Evidence:</strong> {violation.evidence}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {violationsBySeverity.medium.length > 0 && (
                <div className={styles.violationGroup}>
                  <h4 className={styles.severityHeader}>
                    <Badge variant="warning">Medium Severity</Badge>
                    <span className={styles.count}>({violationsBySeverity.medium.length})</span>
                  </h4>
                  {violationsBySeverity.medium.map((violation) => (
                    <div key={violation.id} className={styles.violation}>
                      <div className={styles.violationHeader}>
                        <span className={styles.category}>{violation.category}</span>
                        {violation.confidence && (
                          <span className={styles.confidence}>
                            Confidence: {Math.round(violation.confidence * 100)}%
                          </span>
                        )}
                      </div>
                      <div className={styles.ruleViolated}>{violation.rule_violated}</div>
                      {violation.explanation && (
                        <p className={styles.explanation}>{violation.explanation}</p>
                      )}
                      {violation.evidence && (
                        <div className={styles.evidence}>
                          <strong>Evidence:</strong> {violation.evidence}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {violationsBySeverity.low.length > 0 && (
                <div className={styles.violationGroup}>
                  <h4 className={styles.severityHeader}>
                    <Badge variant="secondary">Low Severity</Badge>
                    <span className={styles.count}>({violationsBySeverity.low.length})</span>
                  </h4>
                  {violationsBySeverity.low.map((violation) => (
                    <div key={violation.id} className={styles.violation}>
                      <div className={styles.violationHeader}>
                        <span className={styles.category}>{violation.category}</span>
                        {violation.confidence && (
                          <span className={styles.confidence}>
                            Confidence: {Math.round(violation.confidence * 100)}%
                          </span>
                        )}
                      </div>
                      <div className={styles.ruleViolated}>{violation.rule_violated}</div>
                      {violation.explanation && (
                        <p className={styles.explanation}>{violation.explanation}</p>
                      )}
                      {violation.evidence && (
                        <div className={styles.evidence}>
                          <strong>Evidence:</strong> {violation.evidence}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className={styles.section}>
              <div className={styles.noViolations}>
                <CheckCircle size={48} />
                <p>No violations found!</p>
              </div>
            </div>
          )}

          {/* Visual Verifications */}
          {check.visual_verifications && check.visual_verifications.length > 0 && (
            <div className={styles.section}>
              <h3>Visual Verifications ({check.visual_verifications.length})</h3>
              {check.visual_verifications.map((verification) => (
                <div key={verification.id} className={styles.verification}>
                  <div className={styles.verificationHeader}>
                    <span className={verification.is_compliant ? styles.compliant : styles.nonCompliant}>
                      {verification.is_compliant ? '✓' : '✗'} {verification.rule_text}
                    </span>
                    <span className={styles.confidence}>
                      {Math.round(verification.confidence * 100)}% confident
                    </span>
                  </div>
                  {verification.visual_evidence && (
                    <p className={styles.visualEvidence}>{verification.visual_evidence}</p>
                  )}
                  {verification.proximity_description && (
                    <p className={styles.proximityDescription}>
                      <em>{verification.proximity_description}</em>
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Metadata */}
          <div className={styles.metadata}>
            <div className={styles.metadataItem}>
              <span className={styles.metadataLabel}>State:</span>
              <span className={styles.metadataValue}>{check.state_code}</span>
            </div>
            {check.template_id && (
              <div className={styles.metadataItem}>
                <span className={styles.metadataLabel}>Template:</span>
                <span className={styles.metadataValue}>{check.template_id}</span>
              </div>
            )}
            <div className={styles.metadataItem}>
              <span className={styles.metadataLabel}>Check ID:</span>
              <span className={styles.metadataValue}>{check.id}</span>
            </div>
          </div>

          {/* Raw Data / Debug Section */}
          <div className={styles.section}>
            <h3>Raw Scan Data</h3>
            <p className={styles.debugDescription}>
              Review the actual data that was analyzed by the AI. Use this to verify the AI's assessment and fine-tune rules.
            </p>
            <div className={styles.debugButtons}>
              {check.llm_input_text && (
                <Button
                  variant="secondary"
                  size="small"
                  onClick={() => {
                    const newWindow = window.open('', '_blank');
                    if (newWindow) {
                      newWindow.document.write(`
                        <html>
                          <head>
                            <title>LLM Input - Check ${check.id}</title>
                            <style>
                              body {
                                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                                line-height: 1.6;
                                max-width: 1000px;
                                margin: 0 auto;
                                padding: 20px;
                                background: #f5f5f5;
                              }
                              pre {
                                background: white;
                                padding: 20px;
                                border-radius: 8px;
                                overflow-x: auto;
                                white-space: pre-wrap;
                                word-wrap: break-word;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                              }
                            </style>
                          </head>
                          <body>
                            <h1>LLM Input - Check ${check.id}</h1>
                            <p><strong>URL:</strong> ${check.url}</p>
                            <p><strong>State:</strong> ${check.state_code}</p>
                            <hr>
                            <pre>${check.llm_input_text.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>
                          </body>
                        </html>
                      `);
                      newWindow.document.close();
                    }
                  }}
                >
                  <FileText size={16} />
                  View Scraped Text
                </Button>
              )}
              {check.report_path && (
                <Button
                  variant="secondary"
                  size="small"
                  onClick={() => window.open(`${import.meta.env.VITE_API_URL}/api/reports/${check.id}/markdown`, '_blank')}
                >
                  <Download size={16} />
                  Download Report
                </Button>
              )}
              {check.visual_verifications && check.visual_verifications.length > 0 && (
                <Button
                  variant="secondary"
                  size="small"
                  onClick={() => {
                    const screenshot = check.visual_verifications?.[0]?.screenshot_path;
                    if (screenshot) {
                      const filename = screenshot.split('/').pop() || screenshot;
                      window.open(`${import.meta.env.VITE_API_URL}/api/reports/screenshots/${filename}`, '_blank');
                    }
                  }}
                >
                  <Eye size={16} />
                  View Screenshot
                </Button>
              )}
            </div>
          </div>
        </div>

        <div className={styles.footer}>
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
          {onRescan && (
            <Button
              variant="primary"
              onClick={onRescan}
              disabled={isRescanning}
            >
              {isRescanning ? (
                <>
                  <RefreshCw size={16} className={styles.spinning} />
                  Rescanning...
                </>
              ) : (
                <>
                  <RefreshCw size={16} />
                  Rescan
                </>
              )}
            </Button>
          )}
        </div>
      </div>
    </Modal>
  );
};
