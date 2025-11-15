/**
 * 🎯 Honeypot Status Grid
 *
 * Real-time honeypot health monitoring and status visualization.
 * Displays deployment status, activity metrics, and alert conditions.
 *
 * @module HoneypotStatusGrid
 */

"use client";

import React, { useState } from "react";
import {
  formatDateTime,
  formatDate,
  formatTime,
  getTimestamp,
} from "@/utils/dateHelpers";
import styles from "./HoneypotStatusGrid.module.css";

const HoneypotStatusGrid = ({ honeypots = [] }) => {
  const [selectedType, setSelectedType] = useState("all");
  const [sortBy, setSortBy] = useState("activity");

  /**
   * Filter and sort honeypots
   */
  const processedHoneypots = React.useMemo(() => {
    let filtered = [...honeypots];

    // Filter by type
    if (selectedType !== "all") {
      filtered = filtered.filter((h) => h.type === selectedType);
    }

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case "activity":
          return (b.interactions || 0) - (a.interactions || 0);
        case "name":
          return a.name.localeCompare(b.name);
        case "status":
          return a.status.localeCompare(b.status);
        default:
          return 0;
      }
    });

    return filtered;
  }, [honeypots, selectedType, sortBy]);

  /**
   * Get unique honeypot types
   */
  const honeypotTypes = React.useMemo(() => {
    return [...new Set(honeypots.map((h) => h.type))];
  }, [honeypots]);

  /**
   * Get status info
   */
  const getStatusInfo = (status) => {
    const map = {
      active: { color: "#10b981", icon: "🟢", label: "ACTIVE" },
      inactive: { color: "#6b7280", icon: "⚪", label: "INACTIVE" },
      degraded: { color: "#ffaa00", icon: "🟡", label: "DEGRADED" },
      error: { color: "#ff0040", icon: "🔴", label: "ERROR" },
    };
    return map[status] || map.inactive;
  };

  /**
   * Get activity level
   */
  const getActivityLevel = (interactions) => {
    if (interactions >= 100) return { level: "Critical", color: "#ff0040" };
    if (interactions >= 50) return { level: "High", color: "#ff4000" };
    if (interactions >= 10) return { level: "Medium", color: "#ffaa00" };
    if (interactions > 0) return { level: "Low", color: "#10b981" };
    return { level: "None", color: "#6b7280" };
  };

  /**
   * Calculate uptime percentage
   */
  const getUptimePercentage = (honeypot) => {
    // Mock calculation - in real implementation, use actual uptime data
    if (honeypot.status === "active") return 99.9;
    if (honeypot.status === "degraded") return 95.0;
    if (honeypot.status === "inactive") return 0;
    return 85.0;
  };

  return (
    <div className={styles.container}>
      {/* Header with controls */}
      <div className={styles.header}>
        <h3 className={styles.title}>🎯 Honeypot Status Grid</h3>

        <div className={styles.controls}>
          <select
            className={styles.select}
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
          >
            <option value="all">All Types</option>
            {honeypotTypes.map((type) => (
              <option key={type} value={type}>
                {type.toUpperCase()}
              </option>
            ))}
          </select>

          <select
            className={styles.select}
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="activity">Sort by Activity</option>
            <option value="name">Sort by Name</option>
            <option value="status">Sort by Status</option>
          </select>
        </div>
      </div>

      {/* Grid */}
      <div className={styles.grid}>
        {processedHoneypots.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>🎯</div>
            <p className={styles.emptyText}>No honeypots deployed</p>
          </div>
        ) : (
          processedHoneypots.map((honeypot) => {
            const statusInfo = getStatusInfo(honeypot.status);
            const activityLevel = getActivityLevel(honeypot.interactions || 0);
            const uptime = getUptimePercentage(honeypot);

            return (
              <div
                key={honeypot.id}
                className={`${styles.card} ${styles[honeypot.status]}`}
              >
                {/* Card Header */}
                <div className={styles.cardHeader}>
                  <div className={styles.cardTitle}>
                    <span className={styles.cardIcon}>{statusInfo.icon}</span>
                    <span className={styles.cardName}>{honeypot.name}</span>
                  </div>

                  <span
                    className={styles.statusBadge}
                    style={{
                      background: `${statusInfo.color}20`,
                      borderColor: `${statusInfo.color}50`,
                      color: statusInfo.color,
                    }}
                  >
                    {statusInfo.label}
                  </span>
                </div>

                {/* Card Body */}
                <div className={styles.cardBody}>
                  <div className={styles.infoRow}>
                    <span className={styles.infoLabel}>Type:</span>
                    <span className={styles.infoValue}>{honeypot.type}</span>
                  </div>

                  <div className={styles.infoRow}>
                    <span className={styles.infoLabel}>Port:</span>
                    <span className={styles.infoValue}>
                      {honeypot.port || "N/A"}
                    </span>
                  </div>

                  <div className={styles.infoRow}>
                    <span className={styles.infoLabel}>Uptime:</span>
                    <span className={`${styles.infoValue} ${styles.uptime}`}>
                      {uptime}%
                    </span>
                  </div>
                </div>

                {/* Metrics */}
                <div className={styles.metrics}>
                  <div className={styles.metricBox}>
                    <span className={styles.metricValue}>
                      {honeypot.interactions || 0}
                    </span>
                    <span className={styles.metricLabel}>Interactions</span>
                  </div>

                  <div className={styles.metricBox}>
                    <span
                      className={styles.metricValue}
                      style={{ color: activityLevel.color }}
                    >
                      {activityLevel.level}
                    </span>
                    <span className={styles.metricLabel}>Activity</span>
                  </div>
                </div>

                {/* Activity Bar */}
                <div className={styles.activityBar}>
                  <div
                    className={styles.activityFill}
                    style={{
                      width: `${Math.min(((honeypot.interactions || 0) / 100) * 100, 100)}%`,
                      background: activityLevel.color,
                    }}
                  />
                </div>

                {/* Footer */}
                <div className={styles.cardFooter}>
                  <span className={styles.footerText}>
                    Last seen:{" "}
                    {honeypot.last_seen
                      ? formatTime(honeypot.last_seen)
                      : "Never"}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Summary Stats */}
      {processedHoneypots.length > 0 && (
        <div className={styles.summary}>
          <div className={styles.summaryItem}>
            <span className={styles.summaryLabel}>Total:</span>
            <span className={styles.summaryValue}>
              {processedHoneypots.length}
            </span>
          </div>
          <div className={styles.summaryItem}>
            <span className={styles.summaryLabel}>Active:</span>
            <span className={`${styles.summaryValue} ${styles.active}`}>
              {processedHoneypots.filter((h) => h.status === "active").length}
            </span>
          </div>
          <div className={styles.summaryItem}>
            <span className={styles.summaryLabel}>Total Interactions:</span>
            <span className={styles.summaryValue}>
              {processedHoneypots.reduce(
                (sum, h) => sum + (h.interactions || 0),
                0,
              )}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default HoneypotStatusGrid;
