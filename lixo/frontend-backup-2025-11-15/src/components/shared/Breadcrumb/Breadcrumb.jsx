/**
 * Breadcrumb Navigation Component
 * Provides hierarchical navigation trail for user orientation
 */
import React from 'react';
import PropTypes from 'prop-types';

export const Breadcrumb = ({ items, separator = '›', className = '' }) => {
  return (
    <nav 
      aria-label="Breadcrumb" 
      className={`flex items-center space-x-2 text-sm ${className}`}
    >
      <ol className="flex items-center space-x-2">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          return (
            <li key={index} className="flex items-center space-x-2">
              {item.onClick ? (
                <button
                  onClick={item.onClick}
                  className="text-green-400/70 hover:text-green-400 transition-colors focus:outline-none focus:ring-2 focus:ring-green-400/50 rounded px-1"
                  aria-current={isLast ? 'page' : undefined}
                >
                  {item.icon && <span className="mr-1" aria-hidden="true">{item.icon}</span>}
                  {item.label}
                </button>
              ) : (
                <span 
                  className={isLast ? 'text-green-400 font-bold' : 'text-green-400/50'}
                  aria-current={isLast ? 'page' : undefined}
                >
                  {item.icon && <span className="mr-1" aria-hidden="true">{item.icon}</span>}
                  {item.label}
                </span>
              )}
              {!isLast && (
                <span className="text-green-400/30" aria-hidden="true">{separator}</span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

Breadcrumb.propTypes = {
  items: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.string.isRequired,
      icon: PropTypes.string,
      onClick: PropTypes.func
    })
  ).isRequired,
  separator: PropTypes.string,
  className: PropTypes.string
};
