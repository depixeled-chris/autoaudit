import { Modal } from '../Modal/Modal';
import { CheckCircle, XCircle, AlertCircle, Info } from 'lucide-react';
import styles from './Alert.module.scss';

export type AlertType = 'success' | 'error' | 'warning' | 'info';

export interface AlertProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  message: string;
  type?: AlertType;
}

const iconMap = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertCircle,
  info: Info,
};

const defaultTitles = {
  success: 'Success',
  error: 'Error',
  warning: 'Warning',
  info: 'Information',
};

export function Alert({
  isOpen,
  onClose,
  title,
  message,
  type = 'info',
}: AlertProps) {
  const Icon = iconMap[type];

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="small" showCloseButton={false}>
      <div className={`${styles.alert} ${styles[type]}`}>
        <div className={styles.iconWrapper}>
          <Icon size={48} className={styles.icon} />
        </div>

        <h2 className={styles.title}>{title || defaultTitles[type]}</h2>

        <div className={styles.message}>
          {message.split('\n').map((line, i) => (
            <p key={i}>{line}</p>
          ))}
        </div>

        <div className={styles.actions}>
          <button onClick={onClose} className={styles.okButton}>
            OK
          </button>
        </div>
      </div>
    </Modal>
  );
}
