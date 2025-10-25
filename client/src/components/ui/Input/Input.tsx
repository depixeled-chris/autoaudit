import type { InputHTMLAttributes } from 'react';
import styles from './Input.module.scss';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ label, error, className = '', ...props }: InputProps) {
  return (
    <div className={styles.inputWrapper}>
      {label && (
        <label htmlFor={props.id} className={styles.label}>
          {label}
        </label>
      )}
      <input className={`${styles.input} ${error ? styles.error : ''} ${className}`} {...props} />
      {error && <span className={styles.errorMessage}>{error}</span>}
    </div>
  );
}

export interface TextareaProps extends InputHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  rows?: number;
}

export function Textarea({ label, error, className = '', rows = 4, ...props }: TextareaProps) {
  return (
    <div className={styles.inputWrapper}>
      {label && (
        <label htmlFor={props.id} className={styles.label}>
          {label}
        </label>
      )}
      <textarea
        className={`${styles.textarea} ${error ? styles.error : ''} ${className}`}
        rows={rows}
        {...props}
      />
      {error && <span className={styles.errorMessage}>{error}</span>}
    </div>
  );
}
