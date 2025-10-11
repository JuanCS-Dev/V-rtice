/**
 * Accessible Button Component
 * MAXIMUS Vértice - Phase 4C
 * 
 * Drop-in replacement for buttons that ensures accessibility
 */

import React from 'react';
import PropTypes from 'prop-types';

/**
 * Accessible Button - Always use this instead of <button>
 * Ensures proper ARIA, keyboard support, and theming
 */
export const Button = ({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  disabled = false,
  type = 'button',
  ariaLabel,
  className = '',
  ...rest
}) => {
  const variantClasses = {
    primary: 'bg-primary text-white hover:bg-primary-dark',
    secondary: 'bg-secondary text-white hover:bg-secondary-dark',
    success: 'bg-success text-white hover:bg-success-dark',
    danger: 'bg-error text-white hover:bg-error-dark',
    ghost: 'bg-transparent border border-primary text-primary hover:bg-primary/10',
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  const baseClasses = 'rounded-lg font-medium transition-base focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary disabled:opacity-50 disabled:cursor-not-allowed';

  // If children is only an icon, require aria-label
  const hasOnlyIcon = React.Children.count(children) === 1 && 
    typeof children === 'object' && 
    children.type?.name?.includes('Icon');

  if (hasOnlyIcon && !ariaLabel && !rest['aria-label']) {
    console.warn('Button with only icon needs aria-label');
  }

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      aria-label={ariaLabel || rest['aria-label']}
      {...rest}
    >
      {children}
    </button>
  );
};

Button.propTypes = {
  children: PropTypes.node.isRequired,
  onClick: PropTypes.func,
  variant: PropTypes.oneOf(['primary', 'secondary', 'success', 'danger', 'ghost']),
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
  disabled: PropTypes.bool,
  type: PropTypes.oneOf(['button', 'submit', 'reset']),
  ariaLabel: PropTypes.string,
  className: PropTypes.string,
};

/**
 * Accessible Icon Button - For icon-only buttons
 */
export const IconButton = ({
  icon: Icon,
  label,
  onClick,
  size = 'md',
  variant = 'ghost',
  className = '',
  ...rest
}) => {
  const sizeMap = {
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-12 h-12',
  };

  return (
    <Button
      onClick={onClick}
      variant={variant}
      size={size}
      ariaLabel={label}
      className={`${sizeMap[size]} p-0 flex items-center justify-center ${className}`}
      {...rest}
    >
      <Icon aria-hidden="true" />
    </Button>
  );
};

IconButton.propTypes = {
  icon: PropTypes.elementType.isRequired,
  label: PropTypes.string.isRequired, // Required for accessibility
  onClick: PropTypes.func,
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
  variant: PropTypes.oneOf(['primary', 'secondary', 'success', 'danger', 'ghost']),
  className: PropTypes.string,
};

/**
 * Accessible Clickable Div - Use sparingly, prefer Button when possible
 * For cases where semantic button doesn't work (e.g., cards, list items)
 */
export const Clickable = ({
  children,
  onClick,
  onKeyDown,
  role = 'button',
  tabIndex = 0,
  ariaLabel,
  className = '',
  ...rest
}) => {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick?.(e);
    }
    onKeyDown?.(e);
  };

  return (
    <div
      role={role}
      tabIndex={tabIndex}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      aria-label={ariaLabel}
      className={`cursor-pointer transition-base focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary ${className}`}
      {...rest}
    >
      {children}
    </div>
  );
};

Clickable.propTypes = {
  children: PropTypes.node.isRequired,
  onClick: PropTypes.func,
  onKeyDown: PropTypes.func,
  role: PropTypes.string,
  tabIndex: PropTypes.number,
  ariaLabel: PropTypes.string,
  className: PropTypes.string,
};

export default { Button, IconButton, Clickable };
