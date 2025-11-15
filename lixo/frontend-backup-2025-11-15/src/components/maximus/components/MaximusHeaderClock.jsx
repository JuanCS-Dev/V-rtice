/**
 * MaximusHeaderClock - Real-time Clock Display
 *
 * Displays current time and date in pt-BR format.
 *
 * @param {Date} currentTime - Current time object
 */

import React from "react";
import PropTypes from "prop-types";
import { formatTime, formatDate } from "../../../utils/dateHelpers";

export const MaximusHeaderClock = ({ currentTime }) => {
  return (
    <div className="header-clock">
      <div className="clock-time">{formatTime(currentTime, "--:--:--")}</div>
      <div className="clock-date">
        {formatDate(currentTime, { dateStyle: "short" }, "N/A")}
      </div>
    </div>
  );
};

MaximusHeaderClock.propTypes = {
  currentTime: PropTypes.instanceOf(Date).isRequired,
};

export default MaximusHeaderClock;
