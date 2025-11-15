/**
 * Immune System Dashboard - Adaptive Biomimetic Security
 * Self-Healing Infrastructure & Digital Immune Cells
 */

import React from "react";

export const ImmuneSystemDashboard = ({ setCurrentView }) => {
  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #0a4d3c 0%, #1a5e4a 100%)",
        color: "#fff",
        padding: "40px",
      }}
    >
      <header style={{ marginBottom: "40px" }}>
        <button
          onClick={() => setCurrentView("main")}
          style={{
            background: "rgba(255,255,255,0.1)",
            border: "1px solid rgba(255,255,255,0.2)",
            color: "#fff",
            padding: "10px 20px",
            cursor: "pointer",
            marginBottom: "20px",
          }}
        >
          ← Back to Home
        </button>
        <h1 style={{ fontSize: "3rem", marginBottom: "10px" }}>
          🧬 Adaptive Immunity
        </h1>
        <p style={{ fontSize: "1.2rem", opacity: 0.8 }}>
          Biomimetic Self-Healing Security Infrastructure
        </p>
      </header>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))",
          gap: "20px",
        }}
      >
        {/* Digital Immune Cells */}
        <div
          data-testid="immune-cells-activity"
          style={{
            background: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: "8px",
            padding: "30px",
          }}
        >
          <h2 style={{ marginBottom: "20px" }}>🦠 Digital Immune Cells</h2>
          <div style={{ marginBottom: "20px" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: "10px",
              }}
            >
              <span>T-Cells (Detection)</span>
              <span style={{ color: "#00ff00" }}>127 Active</span>
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: "10px",
              }}
            >
              <span>B-Cells (Memory)</span>
              <span style={{ color: "#00ff00" }}>2,453 Patterns</span>
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: "10px",
              }}
            >
              <span>NK-Cells (Response)</span>
              <span style={{ color: "#ffaa00" }}>8 Engaged</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span>Macrophages (Cleanup)</span>
              <span style={{ color: "#00ff00" }}>42 Active</span>
            </div>
          </div>
          <div
            style={{
              height: "150px",
              background: "rgba(0, 255, 0, 0.1)",
              borderRadius: "4px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1.5rem",
              border: "1px solid rgba(0, 255, 0, 0.3)",
            }}
          >
            🦠 Immune Cell Network Active
          </div>
        </div>

        {/* Honeypots & Deception */}
        <div
          style={{
            background: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: "8px",
            padding: "30px",
          }}
        >
          <h2 style={{ marginBottom: "20px" }}>🍯 Intelligent Honeypots</h2>
          <ul style={{ listStyle: "none", padding: 0 }}>
            {[
              { name: "SSH Honeypot", status: "ACTIVE", interactions: 34 },
              { name: "HTTP Decoy", status: "LEARNING", interactions: 127 },
              { name: "Database Trap", status: "ACTIVE", interactions: 8 },
            ].map((hp, i) => (
              <li
                key={i}
                style={{
                  background: "rgba(255,255,255,0.03)",
                  padding: "15px",
                  marginBottom: "10px",
                  borderRadius: "4px",
                  borderLeft: `4px solid ${hp.status === "ACTIVE" ? "#00ff00" : "#ffaa00"}`,
                }}
              >
                <strong>{hp.name}</strong>
                <div
                  style={{ fontSize: "0.9rem", marginTop: "5px", opacity: 0.7 }}
                >
                  Status: {hp.status} • {hp.interactions} interactions today
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Self-Healing Stats */}
        <div
          style={{
            background: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: "8px",
            padding: "30px",
          }}
        >
          <h2 style={{ marginBottom: "20px" }}>🔄 Auto-Healing Activity</h2>
          <div style={{ fontSize: "0.9rem" }}>
            <div style={{ marginBottom: "15px" }}>
              <strong style={{ display: "block", marginBottom: "5px" }}>
                Last 24 Hours:
              </strong>
              <ul style={{ paddingLeft: "20px", marginTop: "10px" }}>
                <li>23 vulnerabilities patched automatically</li>
                <li>7 compromised services restarted</li>
                <li>142 suspicious IPs blacklisted</li>
                <li>5 honeypots adapted to new TTPs</li>
              </ul>
            </div>
            <div
              style={{
                marginTop: "20px",
                padding: "15px",
                background: "rgba(0, 255, 0, 0.1)",
                borderRadius: "4px",
                border: "1px solid rgba(0, 255, 0, 0.3)",
              }}
            >
              <strong>System Resilience: 98.7%</strong>
              <div
                style={{ fontSize: "0.8rem", marginTop: "5px", opacity: 0.7 }}
              >
                +2.3% from last week
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImmuneSystemDashboard;
