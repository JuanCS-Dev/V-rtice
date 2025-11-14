/**
 * Keyboard Navigation Tester
 * MAXIMUS Vértice - Frontend Phase 4
 *
 * Interactive tool to test keyboard navigation across the application
 */

import React, { useState, useEffect } from "react";
import { useToast } from "../shared/Toast";
import styles from "./KeyboardTester.module.css";
import { formatTime } from "@/utils/dateHelpers";

export const KeyboardTester = () => {
  const toast = useToast();
  const [isListening, setIsListening] = useState(false);
  const [keyLog, setKeyLog] = useState([]);
  const [focusPath, setFocusPath] = useState([]);
  const [testResults, setTestResults] = useState({
    tabNavigation: null,
    enterActivation: null,
    spaceActivation: null,
    escapeClose: null,
    arrowNavigation: null,
  });

  useEffect(() => {
    if (!isListening) return;

    const handleKeyDown = (e) => {
      const entry = {
        key: e.key,
        code: e.code,
        timestamp: formatTime(new Date(), "--:--:--"),
        target: e.target.tagName,
        id: e.target.id || "no-id",
        className: e.target.className || "no-class",
      };

      setKeyLog((prev) => [entry, ...prev].slice(0, 20));

      // Test specific keys
      if (e.key === "Tab") {
        setTestResults((prev) => ({ ...prev, tabNavigation: "pass" }));
      } else if (e.key === "Enter" && e.target.tagName === "BUTTON") {
        setTestResults((prev) => ({ ...prev, enterActivation: "pass" }));
      } else if (e.key === " " && e.target.tagName === "BUTTON") {
        setTestResults((prev) => ({ ...prev, spaceActivation: "pass" }));
      } else if (e.key === "Escape") {
        setTestResults((prev) => ({ ...prev, escapeClose: "pass" }));
      } else if (
        ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.key)
      ) {
        setTestResults((prev) => ({ ...prev, arrowNavigation: "pass" }));
      }
    };

    const handleFocus = (e) => {
      const element = {
        tag: e.target.tagName,
        id: e.target.id || "no-id",
        className: e.target.className || "no-class",
        timestamp: formatTime(new Date(), "--:--:--"),
      };
      setFocusPath((prev) => [element, ...prev].slice(0, 10));
    };

    document.addEventListener("keydown", handleKeyDown, true);
    document.addEventListener("focus", handleFocus, true);

    return () => {
      document.removeEventListener("keydown", handleKeyDown, true);
      document.removeEventListener("focus", handleFocus, true);
    };
  }, [isListening]);

  const startTest = () => {
    setIsListening(true);
    setKeyLog([]);
    setFocusPath([]);
    setTestResults({
      tabNavigation: null,
      enterActivation: null,
      spaceActivation: null,
      escapeClose: null,
      arrowNavigation: null,
    });
    toast.info("🎹 Keyboard testing started. Press keys to test...", {
      duration: 3000,
    });
  };

  const stopTest = () => {
    setIsListening(false);
    const passedTests = Object.values(testResults).filter(
      (r) => r === "pass",
    ).length;
    const totalTests = Object.keys(testResults).length;

    toast.success(
      `✅ Test complete: ${passedTests}/${totalTests} patterns detected`,
      {
        duration: 5000,
      },
    );
  };

  const clearLogs = () => {
    setKeyLog([]);
    setFocusPath([]);
  };

  const getTestStatus = (result) => {
    if (result === "pass")
      return { icon: "✅", text: "PASSED", class: styles.pass };
    if (result === "fail")
      return { icon: "❌", text: "FAILED", class: styles.fail };
    return { icon: "⏳", text: "PENDING", class: styles.pending };
  };

  return (
    <div className={styles.tester}>
      <div className={styles.header}>
        <h2>⌨️ Keyboard Navigation Tester</h2>
        <p className={styles.subtitle}>Phase 4: Accessibility Validation</p>
      </div>

      <div className={styles.controls}>
        {!isListening ? (
          <button className={styles.btnStart} onClick={startTest}>
            Start Testing
          </button>
        ) : (
          <button className={styles.btnStop} onClick={stopTest}>
            Stop Testing
          </button>
        )}
        <button className={styles.btnClear} onClick={clearLogs}>
          Clear Logs
        </button>
      </div>

      {isListening && (
        <div className={styles.status}>
          <span className={styles.recording}>🔴 RECORDING</span>
          <span>Press keys and navigate to test...</span>
        </div>
      )}

      <div className={styles.grid}>
        {/* Test Results */}
        <section className={styles.section}>
          <h3>Test Results</h3>
          <div className={styles.testList}>
            {Object.entries(testResults).map(([test, result]) => {
              const status = getTestStatus(result);
              return (
                <div
                  key={test}
                  className={`${styles.testItem} ${status.class}`}
                >
                  <span className={styles.testIcon}>{status.icon}</span>
                  <span className={styles.testName}>
                    {test.replace(/([A-Z])/g, " $1").trim()}
                  </span>
                  <span className={styles.testStatus}>{status.text}</span>
                </div>
              );
            })}
          </div>
        </section>

        {/* Key Log */}
        <section className={styles.section}>
          <h3>Key Press Log</h3>
          <div className={styles.log}>
            {keyLog.length === 0 ? (
              <div className={styles.empty}>No keys pressed yet...</div>
            ) : (
              keyLog.map((entry, i) => (
                <div key={i} className={styles.logEntry}>
                  <span className={styles.logKey}>{entry.key}</span>
                  <span className={styles.logCode}>{entry.code}</span>
                  <span className={styles.logTarget}>
                    {entry.target}#{entry.id}
                  </span>
                  <span className={styles.logTime}>{entry.timestamp}</span>
                </div>
              ))
            )}
          </div>
        </section>

        {/* Focus Path */}
        <section className={styles.section}>
          <h3>Focus Path</h3>
          <div className={styles.log}>
            {focusPath.length === 0 ? (
              <div className={styles.empty}>No focus changes yet...</div>
            ) : (
              focusPath.map((element, i) => (
                <div key={i} className={styles.focusEntry}>
                  <span className={styles.focusIndex}>{i + 1}.</span>
                  <span className={styles.focusTag}>
                    &lt;{element.tag.toLowerCase()}&gt;
                  </span>
                  <span className={styles.focusId}>#{element.id}</span>
                  <span className={styles.focusTime}>{element.timestamp}</span>
                </div>
              ))
            )}
          </div>
        </section>
      </div>

      <div className={styles.instructions}>
        <h3>📝 Test Instructions</h3>
        <ul>
          <li>
            <kbd>Tab</kbd> - Navigate forward through focusable elements
          </li>
          <li>
            <kbd>Shift+Tab</kbd> - Navigate backward
          </li>
          <li>
            <kbd>Enter</kbd> / <kbd>Space</kbd> - Activate buttons/links
          </li>
          <li>
            <kbd>Escape</kbd> - Close modals/overlays
          </li>
          <li>
            <kbd>Arrow Keys</kbd> - Navigate within components
          </li>
          <li>
            <kbd>Home</kbd> / <kbd>End</kbd> - Jump to start/end
          </li>
        </ul>
      </div>

      <div className={styles.tips}>
        <h4>💡 Tips for Manual Testing</h4>
        <ul>
          <li>All interactive elements should be reachable via keyboard</li>
          <li>Focus indicator should be clearly visible</li>
          <li>Tab order should follow visual flow</li>
          <li>No keyboard traps (can always navigate away)</li>
          <li>Custom controls should have appropriate ARIA</li>
        </ul>
      </div>
    </div>
  );
};

export default KeyboardTester;
