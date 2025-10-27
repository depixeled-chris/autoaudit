import { Modal } from '../Modal/Modal';
import { AlertTriangle } from 'lucide-react';
import styles from './Confirm.module.scss';

export interface ConfirmProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'default';
}

export function Confirm({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'default',
}: ConfirmProps) {
  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="small" showCloseButton={false}>
      <div className={`${styles.confirm} ${styles[variant]}`}>
        <div className={styles.iconWrapper}>
          <AlertTriangle size={48} className={styles.icon} />
        </div>

        <h2 className={styles.title}>{title}</h2>

        <div className={styles.message}>
          {message.split('\n').map((line, i) => (
            <p key={i}>{line}</p>
          ))}
        </div>

        <div className={styles.actions}>
          <button onClick={onClose} className={styles.cancelButton}>
            {cancelText}
          </button>
          <button onClick={handleConfirm} className={styles.confirmButton}>
            {confirmText}
          </button>
        </div>
      </div>
    </Modal>
  );
}
