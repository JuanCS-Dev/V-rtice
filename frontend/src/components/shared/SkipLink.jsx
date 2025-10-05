/**
 * SkipLink Component
 *
 * WCAG 2.1 AA - Bypass Blocks (2.4.1)
 * Allows keyboard users to skip navigation and jump to main content
 *
 * Usage:
 * <SkipLink href="#main-content">Skip to main content</SkipLink>
 */

import React from 'react';
import PropTypes from 'prop-types';
import './SkipLink.css';

export const SkipLink = ({
  href = '#main-content',
  children = 'Skip to main content',
  className = ''
}) => {
  const handleClick = (e) => {
    e.preventDefault();

    const target = document.querySelector(href);
    if (target) {
      // Set tabindex to allow focus
      target.setAttribute('tabindex', '-1');

      // Focus the element
      target.focus();

      // Remove tabindex after focus
      setTimeout(() => {
        target.removeAttribute('tabindex');
      }, 100);

      // Scroll into view
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <a
      href={href}
      className={`skip-link ${className}`}
      onClick={handleClick}
    >
      {children}
    </a>
  );
};

SkipLink.propTypes = {
  href: PropTypes.string,
  children: PropTypes.node,
  className: PropTypes.string
};

export default SkipLink;
