import type { HTMLAttributes, ReactNode } from 'react';
import styles from './Card.module.scss';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
  children: ReactNode;
}

export function Card({ hover = false, className = '', children, ...props }: CardProps) {
  const classes = [styles.card, hover && styles.hover, className].filter(Boolean).join(' ');

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
}

export interface CardHeaderProps {
  children: ReactNode;
  className?: string;
}

export function CardHeader({ children, className = '' }: CardHeaderProps) {
  return <div className={`${styles.header} ${className}`}>{children}</div>;
}

export interface CardTitleProps {
  children: ReactNode;
  className?: string;
}

export function CardTitle({ children, className = '' }: CardTitleProps) {
  return <h3 className={`${styles.title} ${className}`}>{children}</h3>;
}

export interface CardDescriptionProps {
  children: ReactNode;
  className?: string;
}

export function CardDescription({ children, className = '' }: CardDescriptionProps) {
  return <p className={`${styles.description} ${className}`}>{children}</p>;
}

export interface CardContentProps {
  children: ReactNode;
  className?: string;
}

export function CardContent({ children, className = '' }: CardContentProps) {
  return <div className={`${styles.content} ${className}`}>{children}</div>;
}

export interface CardFooterProps {
  children: ReactNode;
  className?: string;
}

export function CardFooter({ children, className = '' }: CardFooterProps) {
  return <div className={`${styles.footer} ${className}`}>{children}</div>;
}
