/**
 * Monitoring Dashboard - Full Observability Stack
 * Prometheus • Grafana • Jaeger
 */

import React from "react";

export const MonitoringDashboard = ({ setCurrentView }) => {
  return (
    <div
      style={{
        minHeight: "100vh",
        background:
          "linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%)",
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
          📊 Full Observability
        </h1>
        <p style={{ fontSize: "1.2rem", opacity: 0.8 }}>
          Prometheus • Grafana • Jaeger - Complete Monitoring Stack
        </p>
      </header>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))",
          gap: "20px",
        }}
      >
        {/* Prometheus Metrics */}
        <div
          style={{
            background: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: "8px",
            padding: "30px",
          }}
        >
          <h2 style={{ marginBottom: "20px" }}>📈 Prometheus Metrics</h2>
          <div style={{ marginBottom: "15px" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: "10px",
              }}
            >
              <span>Total Metrics Scraped</span>
              <span style={{ color: "#00ff00", fontWeight: "bold" }}>
                127,453
              </span>
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: "10px",
              }}
            >
              <span>Active Targets</span>
              <span style={{ color: "#00ff00", fontWeight: "bold" }}>
                42/42
              </span>
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: "10px",
              }}
            >
              <span>Scrape Duration</span>
              <span style={{ color: "#00ff00", fontWeight: "bold" }}>
                120ms
              </span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span>Storage Size</span>
              <span style={{ color: "#00ff00", fontWeight: "bold" }}>
                2.3 GB
              </span>
            </div>
          </div>
          <div
            style={{
              marginTop: "20px",
              padding: "15px",
              background: "rgba(0, 255, 0, 0.1)",
              borderRadius: "4px",
              border: "1px solid rgba(0, 255, 0, 0.3)",
              textAlign: "center",
            }}
          >
            <div
              style={{ fontSize: "0.8rem", opacity: 0.7, marginBottom: "5px" }}
            >
              System Health
            </div>
            <div style={{ fontSize: "2rem", fontWeight: "bold" }}>99.8%</div>
          </div>
        </div>

        {/* Grafana Dashboards */}
        <div
          style={{
            background: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: "8px",
            padding: "30px",
          }}
        >
          <h2 style={{ marginBottom: "20px" }}>📊 Grafana Dashboards</h2>
          <ul style={{ listStyle: "none", padding: 0 }}>
            {[
              { name: "System Overview", alerts: 0, status: "HEALTHY" },
              { name: "Backend Services", alerts: 2, status: "WARNING" },
              { name: "Database Performance", alerts: 0, status: "HEALTHY" },
              { name: "Network Traffic", alerts: 1, status: "INFO" },
            ].map((dash, i) => (
              <li
                key={i}
                style={{
                  background: "rgba(255,255,255,0.03)",
                  padding: "15px",
                  marginBottom: "10px",
                  borderRadius: "4px",
                  borderLeft: `4px solid ${dash.status === "HEALTHY" ? "#00ff00" : dash.status === "WARNING" ? "#ffaa00" : "#00aaff"}`,
                }}
              >
                <div
                  style={{ display: "flex", justifyContent: "space-between" }}
                >
                  <strong>{dash.name}</strong>
                  <span style={{ fontSize: "0.8rem", opacity: 0.7 }}>
                    {dash.alerts > 0 ? `${dash.alerts} alerts` : "No alerts"}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Jaeger Tracing */}
        <div
          style={{
            background: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: "8px",
            padding: "30px",
          }}
        >
          <h2 style={{ marginBottom: "20px" }}>
            🔍 Jaeger Distributed Tracing
          </h2>
          <div style={{ fontSize: "0.9rem" }}>
            <div style={{ marginBottom: "15px" }}>
              <strong style={{ display: "block", marginBottom: "10px" }}>
                Recent Traces:
              </strong>
              <ul style={{ listStyle: "none", padding: 0 }}>
                {[
                  { service: "maximus-core", duration: "142ms", spans: 23 },
                  { service: "reactive-fabric", duration: "87ms", spans: 15 },
                  { service: "api-gateway", duration: "53ms", spans: 8 },
                ].map((trace, i) => (
                  <li
                    key={i}
                    style={{
                      background: "rgba(255,255,255,0.03)",
                      padding: "10px",
                      marginBottom: "8px",
                      borderRadius: "4px",
                    }}
                  >
                    <div style={{ fontWeight: "bold", marginBottom: "3px" }}>
                      {trace.service}
                    </div>
                    <div style={{ fontSize: "0.8rem", opacity: 0.7 }}>
                      {trace.duration} • {trace.spans} spans
                    </div>
                  </li>
                ))}
              </ul>
            </div>
            <div
              style={{
                marginTop: "20px",
                padding: "15px",
                background: "rgba(0, 170, 255, 0.1)",
                borderRadius: "4px",
                border: "1px solid rgba(0, 170, 255, 0.3)",
              }}
            >
              <strong>Avg Response Time: 94ms</strong>
              <div
                style={{ fontSize: "0.8rem", marginTop: "5px", opacity: 0.7 }}
              >
                -12ms from yesterday
              </div>
            </div>
          </div>
        </div>

        {/* ELK Stack */}
        <div
          style={{
            background: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: "8px",
            padding: "30px",
            gridColumn: "span 3",
          }}
        >
          <h2 style={{ marginBottom: "20px" }}>📝 Centralized Logging (ELK)</h2>
          <div
            style={{
              background: "rgba(0,0,0,0.3)",
              padding: "15px",
              borderRadius: "4px",
              fontFamily: "monospace",
              fontSize: "0.85rem",
              maxHeight: "200px",
              overflowY: "auto",
            }}
          >
            <div style={{ marginBottom: "5px", color: "#00ff00" }}>
              [2025-10-26 12:32:15] INFO maximus-core: Request processed
              successfully
            </div>
            <div style={{ marginBottom: "5px", color: "#00aaff" }}>
              [2025-10-26 12:32:14] DEBUG reactive-fabric: Honeypot interaction
              detected
            </div>
            <div style={{ marginBottom: "5px", color: "#ffaa00" }}>
              [2025-10-26 12:32:13] WARN api-gateway: Rate limit threshold
              reached
            </div>
            <div style={{ marginBottom: "5px", color: "#00ff00" }}>
              [2025-10-26 12:32:12] INFO defensive-ops: Threat neutralized
            </div>
            <div style={{ marginBottom: "5px", color: "#00aaff" }}>
              [2025-10-26 12:32:11] DEBUG maximus-core: Memory optimization
              completed
            </div>
          </div>
          <div style={{ marginTop: "15px", fontSize: "0.85rem", opacity: 0.7 }}>
            Showing last 5 entries • Total logs: 1,234,567
          </div>
        </div>
      </div>
    </div>
  );
};

export default MonitoringDashboard;
