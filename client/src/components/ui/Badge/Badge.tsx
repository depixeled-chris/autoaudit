import type { HTMLAttributes, ReactNode } from 'react';
import styles from './Badge.module.scss';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'success' | 'warning' | 'error' | 'info' | 'neutral';
  children: ReactNode;
}

export function Badge({ variant = 'neutral', className = '', children, ...props }: BadgeProps) {
  const classes = [styles.badge, styles[variant], className].filter(Boolean).join(' ');

  return (
    <span className={classes} {...props}>
      {children}
    </span>
  );
}
