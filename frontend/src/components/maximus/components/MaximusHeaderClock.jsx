/**
 * MaximusHeaderClock - Real-time Clock Display
 *
 * Displays current time and date in pt-BR format.
 *
 * @param {Date} currentTime - Current time object
 */

import React from 'react';
import PropTypes from 'prop-types';

export const MaximusHeaderClock = ({ currentTime }) => {
  return (
    <div className="header-clock">
      <div className="clock-time">{currentTime.toLocaleTimeString('pt-BR')}</div>
      <div className="clock-date">{currentTime.toLocaleDateString('pt-BR')}</div>
    </div>
  );
};

MaximusHeaderClock.propTypes = {
  currentTime: PropTypes.instanceOf(Date).isRequired
};

export default MaximusHeaderClock;
