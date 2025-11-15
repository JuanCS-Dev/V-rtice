/**
 * PanelCard - Generic Panel Container Widget
 *
 * Reusable panel/card container with optional title, icon, and actions.
 * Provides consistent styling across dashboards.
 *
 * Usage:
 * <PanelCard
 *   title="Network Scanner"
 *   icon="🔍"
 *   variant="primary"
 *   actions={<button>Refresh</button>}
 * >
 *   <p>Panel content goes here</p>
 * </PanelCard>
 *
 * @param {string} title - Panel title
 * @param {string} icon - Panel icon (emoji or font icon)
 * @param {string} variant - Color variant (primary, secondary, dark)
 * @param {ReactNode} actions - Action buttons/elements
 * @param {ReactNode} children - Panel content
 * @param {string} className - Additional CSS classes
 */

import React from "react";
import PropTypes from "prop-types";
import "./PanelCard.css";

export const PanelCard = ({
  title,
  icon,
  variant = "primary",
  actions,
  children,
  className = "",
}) => {
  const cardClasses = `panel-card panel-card-${variant} ${className}`;

  return (
    <div className={cardClasses}>
      {(title || icon || actions) && (
        <div className="panel-card-header">
          <div className="panel-card-title-section">
            {icon && (
              <span className="panel-card-icon" aria-hidden="true">
                {icon}
              </span>
            )}
            {title && <h3 className="panel-card-title">{title}</h3>}
          </div>
          {actions && <div className="panel-card-actions">{actions}</div>}
        </div>
      )}
      <div className="panel-card-content">{children}</div>
    </div>
  );
};

PanelCard.propTypes = {
  title: PropTypes.string,
  icon: PropTypes.string,
  variant: PropTypes.oneOf(["primary", "secondary", "dark"]),
  actions: PropTypes.node,
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
};

export default PanelCard;
