/**
 * ModuleContainer - Wrapper for offensive modules
 * Provides consistent container with fade-in animation
 */

import React from "react";
import styles from "./ModuleContainer.module.css";

export const ModuleContainer = ({ children }) => {
  return <div className={styles.container}>{children}</div>;
};
