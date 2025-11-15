/**
 * MaximusTerminal - Terminal Wrapper for Maximus Dashboard
 *
 * Provides proper theming and container sizing for TerminalEmulator
 * when embedded in the Maximus Dashboard.
 */

import React from "react";
import TerminalEmulator from "../terminal/TerminalEmulator";

const MaximusTerminal = () => {
  // Maximus-themed terminal color scheme
  const maximusTheme = {
    background: "#0a0e1a",
    foreground: "#06B6D4",
    cursor: "#8B5CF6",
    cursorAccent: "#000000",
    selection: "rgba(139, 92, 246, 0.3)",
    black: "#000000",
    red: "#EF4444",
    green: "#10B981",
    yellow: "#F59E0B",
    blue: "#3B82F6",
    magenta: "#8B5CF6",
    cyan: "#06B6D4",
    white: "#E2E8F0",
    brightBlack: "#64748B",
    brightRed: "#F87171",
    brightGreen: "#34D399",
    brightYellow: "#FBBF24",
    brightBlue: "#60A5FA",
    brightMagenta: "#A78BFA",
    brightCyan: "#22D3EE",
    brightWhite: "#F1F5F9",
  };

  return (
    <div
      style={{
        width: "100%",
        minHeight: "calc(100vh - 280px)",
        height: "100%",
        background:
          "linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 27, 75, 0.95))",
        border: "2px solid rgba(139, 92, 246, 0.4)",
        borderRadius: "12px",
        overflow: "hidden",
        boxShadow:
          "0 8px 24px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(139, 92, 246, 0.2)",
        position: "relative",
      }}
    >
      {/* Decorative top bar */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: "3px",
          background: "linear-gradient(90deg, #8B5CF6, #06B6D4, #10B981)",
          zIndex: 10,
        }}
      />

      {/* Terminal header label */}
      <div
        style={{
          padding: "0.75rem 1.5rem",
          borderBottom: "1px solid rgba(139, 92, 246, 0.2)",
          background: "rgba(15, 23, 42, 0.8)",
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
        }}
      >
        <div
          style={{
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            background: "linear-gradient(135deg, #10B981, #06B6D4)",
            boxShadow: "0 0 10px rgba(16, 185, 129, 0.6)",
            animation: "pulse 2s ease-in-out infinite",
          }}
        />
        <span
          style={{
            fontSize: "0.85rem",
            fontWeight: "600",
            color: "#94A3B8",
            textTransform: "uppercase",
            letterSpacing: "1px",
            fontFamily: "monospace",
          }}
        >
          ⚡ MAXIMUS Terminal
        </span>
        <span
          style={{
            marginLeft: "auto",
            fontSize: "0.7rem",
            color: "#64748B",
            fontFamily: "monospace",
          }}
        >
          v2.0
        </span>
      </div>

      {/* Terminal component */}
      <div style={{ height: "calc(100% - 50px)" }}>
        <TerminalEmulator theme={maximusTheme} isFullscreen={false} />
      </div>
    </div>
  );
};

export default MaximusTerminal;
