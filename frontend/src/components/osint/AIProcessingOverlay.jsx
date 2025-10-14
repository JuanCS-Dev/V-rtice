/**
 * AIProcessingOverlay - AI Processing Fullscreen Overlay
 *
 * Displays fullscreen overlay with spinning brain icon and progress bar
 * when AI is processing. Includes ARIA attributes for accessibility.
 *
 * @param {boolean} isVisible - Show/hide overlay
 */

import React from 'react';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';

export const AIProcessingOverlay = ({ isVisible }) => {
  const { t } = useTranslation();

  if (!isVisible) return null;

  return (
    <div
      className="absolute top-0 left-0 right-0 bottom-0 bg-black/90 flex items-center justify-center z-50 backdrop-blur-lg"
      role="status"
      aria-live="polite"
      aria-label={t('dashboard.osint.processing')}
    >
      <div className="text-center">
        <div className="text-6xl animate-spin mb-4" aria-hidden="true">
          🧠
        </div>
        <div className="text-red-400 text-xl font-bold mb-4 tracking-wider">
          {t('dashboard.osint.processing')}
        </div>
        <div className="w-80 h-2 bg-red-400/20 rounded-full overflow-hidden">
          <div className="h-full bg-gradient-to-r from-red-400 to-pink-400 animate-pulse"></div>
        </div>
      </div>
    </div>
  );
};

AIProcessingOverlay.propTypes = {
  isVisible: PropTypes.bool.isRequired
};

export default AIProcessingOverlay;
