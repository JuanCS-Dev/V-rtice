/**
 * OSINTFooter - OSINT Dashboard Footer
 *
 * Displays connection status, AI status, operator ID, and classification.
 * Shows AI accuracy metric from systemStats.
 *
 * @param {Object} systemStats - System statistics with aiAccuracy
 */

import React from 'react';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';

export const OSINTFooter = ({ systemStats }) => {
  const { t } = useTranslation();

  return (
    <footer
      className="border-t border-purple-400/30 bg-black/50 backdrop-blur-sm p-2"
      role="contentinfo"
      aria-label={t('accessibility.dashboardFooter')}
    >
      <div className="flex justify-between items-center text-xs">
        <div className="flex space-x-6">
          <span className="text-purple-400" aria-label="Connection status">
            🔒 CONEXÃO: SEGURA
          </span>
          <span className="text-purple-400" aria-label="AI status">
            🧠 AURORA AI: ATIVO
          </span>
          <span className="text-purple-400" aria-label="Operator ID">
            👤 OPERADOR: OSINT_OPS_001
          </span>
          <span
            className="text-purple-400"
            aria-label={`AI accuracy: ${systemStats.aiAccuracy} percent`}
          >
            📊 PRECISÃO IA: {systemStats.aiAccuracy}%
          </span>
        </div>
        <div className="text-purple-400/70">
          MÓDULO OSINT INTELLIGENCE | PROJETO VÉRTICE v3.0 | SSP-GO | CLASSIFICAÇÃO: CONFIDENCIAL
        </div>
      </div>
    </footer>
  );
};

OSINTFooter.propTypes = {
  systemStats: PropTypes.shape({
    aiAccuracy: PropTypes.number.isRequired
  }).isRequired
};

export default OSINTFooter;
