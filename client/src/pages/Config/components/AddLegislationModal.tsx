import { useState, useRef } from 'react';
import { useCreateLegislationSourceMutation } from '@services/api/statesApi';
import apiClient from '@lib/api/axios';
import { useDispatch } from 'react-redux';
import { apiSlice } from '@store/api/apiSlice';
import styles from './Modal.module.scss';

interface Props {
  stateCode: string;
  onClose: () => void;
}

type TabType = 'manual' | 'upload';

export default function AddLegislationModal({ stateCode, onClose }: Props) {
  const dispatch = useDispatch();
  const [activeTab, setActiveTab] = useState<TabType>('upload');
  const [form, setForm] = useState({
    statute_number: '',
    title: '',
    full_text: '',
    source_url: '',
    applies_to_page_types: '',
  });
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [createLegislation, { isLoading }] = useCreateLegislationSourceMutation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createLegislation({ ...form, state_code: stateCode }).unwrap();
      onClose();
    } catch (error) {
      console.error('Failed:', error);
    }
  };

  const handleFileSelect = (file: File) => {
    // Validate file type
    const validTypes = ['application/pdf', 'text/markdown', 'text/plain'];
    const validExtensions = ['.pdf', '.md', '.txt'];
    const hasValidType = validTypes.includes(file.type);
    const hasValidExtension = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));

    if (!hasValidType && !hasValidExtension) {
      setUploadError('Invalid file type. Please upload a PDF, Markdown (.md), or Plain Text (.txt) file.');
      return;
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB
      setUploadError('File too large. Maximum size is 10MB.');
      return;
    }

    setUploadFile(file);
    setUploadError(null);
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleUploadSubmit = async () => {
    if (!uploadFile) return;

    setUploadLoading(true);
    setUploadError(null);

    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('state_code', stateCode);

      const response = await apiClient.post('/api/states/legislation/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      console.log('Upload success:', response.data);

      // Invalidate RTK Query cache to refresh legislation list
      dispatch(apiSlice.util.invalidateTags(['States']));

      // Show success message
      setUploadSuccess(true);
    } catch (error: any) {
      console.error('Upload failed:', error);
      setUploadError(error.response?.data?.detail || 'Failed to upload and digest document');
    } finally {
      setUploadLoading(false);
    }
  };

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={`${styles.modal} ${styles.large}`} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h2>Add Legislation Source - {stateCode}</h2>
          <button className={styles.closeButton} onClick={onClose}>×</button>
        </div>

        <div className={styles.tabs}>
          <button
            className={`${styles.tab} ${activeTab === 'upload' ? styles.active : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            Upload Document
          </button>
          <button
            className={`${styles.tab} ${activeTab === 'manual' ? styles.active : ''}`}
            onClick={() => setActiveTab('manual')}
          >
            Manual Entry
          </button>
        </div>

        {activeTab === 'upload' ? (
          uploadSuccess ? (
            <div className={styles.uploadSuccess}>
              <div className={styles.successIcon}>✅</div>
              <h3>Legislation Uploaded Successfully!</h3>
              <p>Your document has been digested and the legislation source has been created.</p>

              <div className={styles.nextSteps}>
                <h4>Next Steps:</h4>
                <ol>
                  <li>Close this modal to return to the state configuration</li>
                  <li>Click on the newly created legislation source to view details</li>
                  <li>Click the <strong>"Re-digest"</strong> button to generate compliance rules from the legislation</li>
                  <li>Review and approve the generated rules in the Rules tab</li>
                </ol>
              </div>

              <div className={styles.actions}>
                <button
                  type="button"
                  className={styles.primaryButton}
                  onClick={onClose}
                >
                  Done
                </button>
              </div>
            </div>
          ) : (
          <div className={styles.uploadContainer}>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.md,.txt"
              onChange={handleFileInputChange}
              style={{ display: 'none' }}
            />

            <div
              className={`${styles.dropzone} ${isDragging ? styles.dragging : ''} ${uploadFile ? styles.hasFile : ''}`}
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              {uploadFile ? (
                <div className={styles.fileInfo}>
                  <div className={styles.fileIcon}>📄</div>
                  <div className={styles.fileName}>{uploadFile.name}</div>
                  <div className={styles.fileSize}>
                    {(uploadFile.size / 1024 / 1024).toFixed(2)} MB
                  </div>
                  <button
                    type="button"
                    className={styles.removeFile}
                    onClick={(e) => {
                      e.stopPropagation();
                      setUploadFile(null);
                    }}
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <div className={styles.dropzoneContent}>
                  <div className={styles.uploadIcon}>📁</div>
                  <p className={styles.dropzoneText}>
                    Drag and drop a file here, or click to browse
                  </p>
                  <p className={styles.dropzoneHint}>
                    Supported: PDF, Markdown (.md), Plain Text (.txt)
                  </p>
                  <p className={styles.dropzoneHint}>
                    Maximum file size: 10MB
                  </p>
                </div>
              )}
            </div>

            {uploadError && (
              <div className={styles.errorMessage}>
                {uploadError}
              </div>
            )}

            <div className={styles.uploadInfo}>
              <h3>What happens next?</h3>
              <p>The uploaded document will be analyzed using AI to automatically extract:</p>
              <ul>
                <li>Statute number and title</li>
                <li>Complete undoctored legislative text</li>
                <li>Applicable page types (VDP, HOMEPAGE, etc.)</li>
                <li>Plain language compliance requirements (digests)</li>
              </ul>
              <p className={styles.reviewNote}>
                <strong>Note:</strong> All AI-generated content will require manual review before being used in compliance checks.
              </p>
            </div>

            <div className={styles.actions}>
              <button type="button" className={styles.secondaryButton} onClick={onClose}>
                Cancel
              </button>
              <button
                type="button"
                className={styles.primaryButton}
                onClick={handleUploadSubmit}
                disabled={!uploadFile || uploadLoading}
              >
                {uploadLoading ? 'Uploading & Digesting...' : 'Upload & Digest'}
              </button>
            </div>
          </div>
          )
        ) : (
          <form onSubmit={handleSubmit}>
            <div className={styles.formGroup}>
              <label>Statute Number *</label>
              <input
                value={form.statute_number}
                onChange={(e) => setForm({ ...form, statute_number: e.target.value })}
                placeholder="e.g., OK Stat § 15-766.1"
                required
              />
            </div>
            <div className={styles.formGroup}>
              <label>Title *</label>
              <input
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="Short description of the statute"
                required
              />
            </div>
            <div className={styles.formGroup}>
              <label>Full Text (Undoctored) *</label>
              <textarea
                value={form.full_text}
                onChange={(e) => setForm({ ...form, full_text: e.target.value })}
                placeholder="Paste the complete, unmodified statutory text here..."
                rows={10}
                required
              />
            </div>
            <div className={styles.formGroup}>
              <label>Source URL</label>
              <input
                value={form.source_url}
                onChange={(e) => setForm({ ...form, source_url: e.target.value })}
                placeholder="https://..."
              />
            </div>
            <div className={styles.formGroup}>
              <label>Applies To Page Types (comma-separated)</label>
              <input
                value={form.applies_to_page_types}
                onChange={(e) => setForm({ ...form, applies_to_page_types: e.target.value })}
                placeholder="VDP, HOMEPAGE, FINANCING"
              />
            </div>
            <div className={styles.actions}>
              <button type="button" className={styles.secondaryButton} onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className={styles.primaryButton} disabled={isLoading}>
                {isLoading ? 'Adding...' : 'Add Legislation'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
