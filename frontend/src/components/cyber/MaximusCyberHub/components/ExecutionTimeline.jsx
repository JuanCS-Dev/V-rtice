import React from "react";
import styles from "./ExecutionTimeline.module.css";
import { formatTime } from "../../../../utils/dateHelpers";

export const ExecutionTimeline = ({ analysisSteps }) => {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>Execution Timeline</h3>
      </div>

      {analysisSteps.length === 0 ? (
        <div className={styles.empty}>
          <div className={styles.emptyIcon}>🛡️</div>
          <p className={styles.emptyText}>Awaiting investigation start</p>
        </div>
      ) : (
        <div className={styles.timeline}>
          {analysisSteps.map((step, idx) => (
            <div key={idx} className={styles.step}>
              <div className={styles.stepIcon}>
                {step.status === "running" && (
                  <div className={styles.spinner}></div>
                )}
                {step.status === "completed" && (
                  <span className={styles.iconCompleted}>✅</span>
                )}
                {step.status === "warning" && (
                  <span className={styles.iconWarning}>⚠️</span>
                )}
                {step.status === "failed" && (
                  <span className={styles.iconFailed}>❌</span>
                )}
              </div>
              <div className={styles.stepContent}>
                <div className={`${styles.message} ${styles[step.status]}`}>
                  {step.message}
                </div>
                <div className={styles.timestamp}>
                  {formatTime(step.timestamp, "--:--:--")}
                </div>
                {step.result && (
                  <div className={styles.result}>
                    <pre className={styles.resultContent}>
                      {JSON.stringify(step.result, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
