/**
 * ModuleStatusCard - Module Status Display Widget
 *
 * Displays module name, online/offline status, and activity description.
 * Used in OSINT overview and other module status displays.
 *
 * Usage:
 * <ModuleStatusCard
 *   name="Maximus AI Engine"
 *   status="online"
 *   activity="Analyzing patterns..."
 * />
 *
 * @param {string} name - Module name
 * @param {string} status - Module status (online, offline, degraded, idle)
 * @param {string} activity - Current activity description
 * @param {string} className - Additional CSS classes
 */

import React from "react";
import PropTypes from "prop-types";
import "./ModuleStatusCard.css";

const STATUS_CONFIG = {
  online: { dot: "status-dot-online", label: "Online" },
  offline: { dot: "status-dot-offline", label: "Offline" },
  degraded: { dot: "status-dot-degraded", label: "Degraded" },
  idle: { dot: "status-dot-idle", label: "Idle" },
  running: { dot: "status-dot-running", label: "Running" },
};

export const ModuleStatusCard = ({
  name,
  status = "online",
  activity,
  className = "",
}) => {
  const statusConfig = STATUS_CONFIG[status] || STATUS_CONFIG.online;

  return (
    <div className={`module-status-card ${className}`}>
      <div className="module-status-header">
        <span className="module-status-name">{name}</span>
        <div
          className={`module-status-dot ${statusConfig.dot}`}
          aria-label={`Status: ${statusConfig.label}`}
        ></div>
      </div>
      {activity && <div className="module-status-activity">{activity}</div>}
    </div>
  );
};

ModuleStatusCard.propTypes = {
  name: PropTypes.string.isRequired,
  status: PropTypes.oneOf(["online", "offline", "degraded", "idle", "running"]),
  activity: PropTypes.string,
  className: PropTypes.string,
};

export default ModuleStatusCard;
