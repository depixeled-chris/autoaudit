import styles from './Toggle.module.scss';

export interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  size?: 'small' | 'medium';
}

export function Toggle({ checked, onChange, disabled = false, size = 'medium' }: ToggleProps) {
  const handleClick = () => {
    if (!disabled) {
      onChange(!checked);
    }
  };

  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      className={`${styles.toggle} ${checked ? styles.checked : ''} ${
        disabled ? styles.disabled : ''
      } ${styles[size]}`}
      onClick={handleClick}
      disabled={disabled}
    >
      <span className={styles.slider} />
    </button>
  );
}
