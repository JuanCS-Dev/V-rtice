import React from 'react';
import styles from './Badge.module.css';

export const Badge = ({
  children,
  variant = 'default',
  size = 'md',
  pill = false,
  className = '',
  ...props
}) => {
  const badgeClasses = [
    styles.badge,
    styles[variant],
    styles[size],
    pill && styles.pill,
    className
  ].filter(Boolean).join(' ');

  return (
    <span className={badgeClasses} {...props}>
      {children}
    </span>
  );
};

export default Badge;
