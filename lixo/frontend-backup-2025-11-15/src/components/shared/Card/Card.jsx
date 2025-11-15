import React from 'react';
import styles from './Card.module.css';

export const Card = ({
  title,
  subtitle,
  badge,
  children,
  variant = 'cyber',
  padding = 'md',
  hoverable = false,
  className = '',
  headerActions,
  footer,
  ...props
}) => {
  const cardClasses = [
    styles.card,
    styles[variant],
    styles[`padding-${padding}`],
    hoverable && styles.hoverable,
    className
  ].filter(Boolean).join(' ');

  return (
    <div className={cardClasses} {...props}>
      {(title || subtitle || badge || headerActions) && (
        <div className={styles.header}>
          <div className={styles.headerContent}>
            {title && (
              <div className={styles.titleWrapper}>
                <h3 className={styles.title}>{title}</h3>
                {badge && <span className={styles.badge}>{badge}</span>}
              </div>
            )}
            {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
          </div>
          {headerActions && (
            <div className={styles.headerActions}>{headerActions}</div>
          )}
        </div>
      )}

      <div className={styles.content}>{children}</div>

      {footer && <div className={styles.footer}>{footer}</div>}
    </div>
  );
};

export default Card;
