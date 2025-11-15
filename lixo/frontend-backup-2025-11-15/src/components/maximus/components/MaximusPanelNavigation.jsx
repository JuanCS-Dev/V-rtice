/**
 * MaximusPanelNavigation - Panel Tabs Navigation
 *
 * Displays clickable panel tabs with keyboard navigation support.
 * Shows panel icon, name, and description.
 *
 * @param {Array} panels - Array of panel objects
 * @param {string} activePanel - Currently active panel ID
 * @param {Function} setActivePanel - Function to change active panel
 * @param {Object} getItemProps - Keyboard navigation props from useKeyboardNavigation
 */

import React from "react";
import PropTypes from "prop-types";

export const MaximusPanelNavigation = ({
  panels,
  activePanel,
  setActivePanel,
  getItemProps,
}) => {
  return (
    <div className="panel-navigation">
      {panels.map((panel, index) => (
        <button
          key={panel.id}
          {...getItemProps(index, {
            onClick: () => setActivePanel(panel.id),
            className: `panel-tab ${activePanel === panel.id ? "panel-tab-active" : ""}`,
          })}
        >
          <span className="panel-icon">{panel.icon}</span>
          <div className="panel-info">
            <span className="panel-name">{panel.name}</span>
            <span className="panel-desc">{panel.description}</span>
          </div>
        </button>
      ))}
    </div>
  );
};

MaximusPanelNavigation.propTypes = {
  panels: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
      icon: PropTypes.string.isRequired,
      description: PropTypes.string.isRequired,
    }),
  ).isRequired,
  activePanel: PropTypes.string.isRequired,
  setActivePanel: PropTypes.func.isRequired,
  getItemProps: PropTypes.func.isRequired,
};

export default MaximusPanelNavigation;
