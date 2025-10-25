import { useEffect, useRef } from 'react';
import type { ReactNode } from 'react';
import { X } from 'lucide-react';
import styles from './Modal.module.scss';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  size?: 'small' | 'medium' | 'large';
  showCloseButton?: boolean;
}

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = 'medium',
  showCloseButton = true,
}: ModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const mouseDownTargetRef = useRef<EventTarget | null>(null);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  // Track where mouse down occurred
  const handleMouseDown = (e: React.MouseEvent) => {
    mouseDownTargetRef.current = e.target;
  };

  // Only close if both mousedown and mouseup happened on the overlay
  const handleOverlayClick = (e: React.MouseEvent) => {
    if (
      e.target === overlayRef.current &&
      mouseDownTargetRef.current === overlayRef.current
    ) {
      onClose();
    }
    mouseDownTargetRef.current = null;
  };

  if (!isOpen) return null;

  return (
    <div
      ref={overlayRef}
      className={styles.overlay}
      onMouseDown={handleMouseDown}
      onClick={handleOverlayClick}
    >
      <div className={`${styles.modal} ${styles[size]}`}>
        {(title || showCloseButton) && (
          <div className={styles.header}>
            {title && <h2 className={styles.title}>{title}</h2>}
            {showCloseButton && (
              <button
                onClick={onClose}
                className={styles.closeButton}
                aria-label="Close modal"
              >
                <X size={20} />
              </button>
            )}
          </div>
        )}

        <div className={styles.content}>{children}</div>
      </div>
    </div>
  );
}
