/**
 * MaximusStatusIndicators - AI Service Status Display
 *
 * Displays status for CORE, ORACLE, and EUREKA services.
 * Uses StatusIndicator component for consistency.
 *
 * @param {Object} aiStatus - AI service status object
 * @param {Function} getStatusColor - Status color mapping function
 */

import React from 'react';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import { StatusIndicator } from './StatusIndicator';

export const MaximusStatusIndicators = ({ aiStatus, getStatusColor }) => {
  const { t } = useTranslation();

  return (
    <div
      className="status-indicators"
      style={{
        display: 'flex',
        gap: '1.5rem',
        maxWidth: '600px'
      }}
    >
      <StatusIndicator
        label={t('dashboard.maximus.status.core')}
        status={aiStatus.core.status}
        getStatusColor={getStatusColor}
        t={t}
      />
      <StatusIndicator
        label={t('dashboard.maximus.status.oracle')}
        status={aiStatus.oraculo.status}
        getStatusColor={getStatusColor}
        t={t}
      />
      <StatusIndicator
        label={t('dashboard.maximus.status.eureka')}
        status={aiStatus.eureka.status}
        getStatusColor={getStatusColor}
        t={t}
      />
    </div>
  );
};

MaximusStatusIndicators.propTypes = {
  aiStatus: PropTypes.shape({
    core: PropTypes.shape({
      status: PropTypes.string.isRequired
    }).isRequired,
    oraculo: PropTypes.shape({
      status: PropTypes.string.isRequired
    }).isRequired,
    eureka: PropTypes.shape({
      status: PropTypes.string.isRequired
    }).isRequired
  }).isRequired,
  getStatusColor: PropTypes.func.isRequired
};

export default MaximusStatusIndicators;
