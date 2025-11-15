/**
 * MaximusHeader - Command Center Header (MODULAR)
 *
 * Two-tier design:
 * - Top Bar: Logo, Status, Clock, Actions
 * - Nav Bar: Panel Navigation
 *
 * 🎯 ZERO INLINE STYLES - 100% CSS Variables
 * ✅ Tema-agnóstico (Matrix + Enterprise)
 * ✅ Responsivo nato
 * ✅ Sem truncamento
 */

import React from "react";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import { CompactEffectSelector } from "./CompactEffectSelector";
import { CompactLanguageSelector } from "./CompactLanguageSelector";
import { formatTime, formatDate } from "../../../utils/dateHelpers";
import styles from "./MaximusHeader.module.css";

export const MaximusHeader = ({
  aiStatus,
  currentTime,
  activePanel,
  panels,
  setActivePanel,
  setCurrentView,
  getItemProps,
  backgroundEffect,
  onEffectChange,
}) => {
  const { t: _t } = useTranslation();

  // Format time
  const timeString = formatTime(currentTime, "--:--:--");
  const dateString = formatDate(currentTime, { dateStyle: "short" }, "N/A");

  return (
    <header className={styles.header}>
      {/* TOP BAR - Command Center */}
      <div className={styles.topBar}>
        {/* LEFT - Logo & Branding */}
        <div className={styles.branding}>
          <div className={styles.logoContainer}>
            🧠
            <div className={styles.logoPulse}></div>
          </div>
          <div className={styles.logoText}>
            <h1 className={styles.logoTitle}>MAXIMUS AI</h1>
            <p className={styles.logoSubtitle}>
              Autonomous Intelligence Platform
            </p>
          </div>
        </div>

        {/* CENTER - Status Indicators */}
        <div className={styles.statusIndicators}>
          {/* CORE */}
          <div className={styles.statusCard}>
            <div
              className={`${styles.statusTop} ${styles[aiStatus.core.status]}`}
            ></div>
            <span className={styles.statusLabel}>CORE</span>
            <span
              className={`${styles.statusValue} ${styles[aiStatus.core.status]}`}
            >
              {aiStatus.core.status === "online"
                ? "ONLINE"
                : aiStatus.core.status === "offline"
                  ? "OFFLINE"
                  : "IDLE"}
            </span>
          </div>

          {/* ORACLE */}
          <div className={styles.statusCard}>
            <div
              className={`${styles.statusTop} ${styles[aiStatus.oraculo.status]}`}
            ></div>
            <span className={styles.statusLabel}>ORACLE</span>
            <span
              className={`${styles.statusValue} ${styles[aiStatus.oraculo.status]}`}
            >
              {aiStatus.oraculo.status === "online"
                ? "IDLE"
                : aiStatus.oraculo.status === "offline"
                  ? "OFFLINE"
                  : "IDLE"}
            </span>
          </div>

          {/* EUREKA */}
          <div className={styles.statusCard}>
            <div
              className={`${styles.statusTop} ${styles[aiStatus.eureka.status]}`}
            ></div>
            <span className={styles.statusLabel}>EUREKA</span>
            <span
              className={`${styles.statusValue} ${styles[aiStatus.eureka.status]}`}
            >
              {aiStatus.eureka.status === "online"
                ? "IDLE"
                : aiStatus.eureka.status === "offline"
                  ? "OFFLINE"
                  : "IDLE"}
            </span>
          </div>
        </div>

        {/* RIGHT - Time, Effects, Back */}
        <div className={styles.actions}>
          {/* Clock */}
          <div className={styles.clock}>
            <span className={styles.clockTime}>{timeString}</span>
            <span className={styles.clockDate}>{dateString}</span>
          </div>

          {/* Language Selector */}
          <CompactLanguageSelector />

          {/* Effect Selector */}
          <CompactEffectSelector
            currentEffect={backgroundEffect}
            onEffectChange={onEffectChange}
          />

          {/* Back Button */}
          <button
            onClick={() => setCurrentView("main")}
            className={styles.backButton}
            aria-label="Back to main view"
          >
            ← BACK
          </button>
        </div>
      </div>

      {/* NAVIGATION BAR - Panel Selection */}
      <div className={styles.navBar}>
        {panels.map((panel, index) => {
          const isActive = activePanel === panel.id;
          const itemProps = getItemProps ? getItemProps(index) : {};

          return (
            <button
              key={panel.id}
              onClick={() => setActivePanel(panel.id)}
              {...itemProps}
              className={`${styles.navButton} ${isActive ? styles.active : styles.inactive}`}
              aria-label={`Navigate to ${panel.name}`}
              aria-current={isActive ? "page" : undefined}
            >
              {isActive && <div className={styles.navUnderline}></div>}
              <span className={styles.navIcon}>{panel.icon}</span>
              <span className={styles.navLabel}>{panel.name}</span>
            </button>
          );
        })}
      </div>
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
  backgroundEffect: PropTypes.string,
  onEffectChange: PropTypes.func,
};

export default MaximusHeader;
