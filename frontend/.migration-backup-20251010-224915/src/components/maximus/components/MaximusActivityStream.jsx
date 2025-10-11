/**
 * MaximusActivityStream - AI Brain Activity Footer
 *
 * Displays real-time AI activity events in a stream.
 * Shows last 5 events with severity-based styling.
 *
 * @param {Array} brainActivity - Array of activity events
 */

import React from 'react';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import { ActivityItem } from '../../shared/widgets';

export const MaximusActivityStream = ({ brainActivity }) => {
  const { t } = useTranslation();

  return (
    <footer className="maximus-footer">
      <div className="footer-header">
        <span className="footer-title">🧠 {t('dashboard.maximus.footer.brainActivity')}</span>
        <span className="footer-count">
          {brainActivity.length} {t('dashboard.maximus.footer.eventsRegistered')}
        </span>
      </div>
      <div className="activity-stream">
        {brainActivity.length === 0 ? (
          <div className="activity-empty">
            <span>⏳ {t('dashboard.maximus.footer.waitingActivity')}</span>
          </div>
        ) : (
          brainActivity.slice(0, 5).map(activity => (
            <ActivityItem
              key={activity.id}
              timestamp={activity.timestamp}
              type={activity.type}
              action={activity.action}
              severity={activity.severity}
            />
          ))
        )}
      </div>
    </footer>
  );
};

MaximusActivityStream.propTypes = {
  brainActivity: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      type: PropTypes.string.isRequired,
      action: PropTypes.string.isRequired,
      severity: PropTypes.oneOf(['info', 'success', 'warning', 'critical']).isRequired,
      timestamp: PropTypes.string.isRequired
    })
  ).isRequired
};

export default MaximusActivityStream;
