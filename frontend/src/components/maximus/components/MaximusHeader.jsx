/**
 * MaximusHeader - Main Dashboard Header
 *
 * Composes all header sub-components:
 * - Logo & Title (MaximusHeaderLogo)
 * - Status Indicators (MaximusStatusIndicators)
 * - Clock (MaximusHeaderClock)
 * - Back Button
 * - Panel Navigation (MaximusPanelNavigation)
 *
 * @param {Object} aiStatus - AI service status
 * @param {Date} currentTime - Current time
 * @param {string} activePanel - Active panel ID
 * @param {Array} panels - Panel configuration array
 * @param {Function} setActivePanel - Panel change handler
 * @param {Function} setCurrentView - View navigation handler
 * @param {Object} getItemProps - Keyboard navigation props
 * @param {Function} getStatusColor - Status color mapping function
 */

import React from 'react';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import { MaximusHeaderLogo } from './MaximusHeaderLogo';
import { MaximusStatusIndicators } from './MaximusStatusIndicators';
import { MaximusHeaderClock } from './MaximusHeaderClock';
import { MaximusPanelNavigation } from './MaximusPanelNavigation';

export const MaximusHeader = ({
  aiStatus,
  currentTime,
  activePanel,
  panels,
  setActivePanel,
  setCurrentView,
  getItemProps,
  getStatusColor
}) => {
  const { t } = useTranslation();

  return (
    <header className="maximus-header">
      <div className="header-content">
        {/* Logo & Title */}
        <MaximusHeaderLogo />

        {/* System Status Indicators */}
        <div className="header-center">
          <MaximusStatusIndicators
            aiStatus={aiStatus}
            getStatusColor={getStatusColor}
          />
        </div>

        {/* Clock & Actions */}
        <div className="header-right">
          <MaximusHeaderClock currentTime={currentTime} />
          <button
            onClick={() => setCurrentView('main')}
            className="btn-back-vertice"
            aria-label={t('navigation.back_to_hub')}
          >
            <span>← {t('common.back').toUpperCase()}</span>
          </button>
        </div>
      </div>

      {/* Panel Navigation */}
      <MaximusPanelNavigation
        panels={panels}
        activePanel={activePanel}
        setActivePanel={setActivePanel}
        getItemProps={getItemProps}
      />
    </header>
  );
};

MaximusHeader.propTypes = {
  aiStatus: PropTypes.object.isRequired,
  currentTime: PropTypes.instanceOf(Date).isRequired,
  activePanel: PropTypes.string.isRequired,
  panels: PropTypes.array.isRequired,
  setActivePanel: PropTypes.func.isRequired,
  setCurrentView: PropTypes.func.isRequired,
  getItemProps: PropTypes.func.isRequired,
  getStatusColor: PropTypes.func.isRequired
};

export default MaximusHeader;
