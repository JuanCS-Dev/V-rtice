/**
 * ═══════════════════════════════════════════════════════════════════════════
 * THREAT PREDICTION WIDGET - FASE 8 Enhanced Cognition
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Visualiza predições de ameaças futuras usando:
 * - Time-series Analysis
 * - Bayesian Inference
 * - Vulnerability Exploitation Forecasting
 */

import React, { useState } from "react";
import { predictThreats } from "../../../api/maximusAI";
import logger from "@/utils/logger";
import "./ThreatPredictionWidget.css";

export const ThreatPredictionWidget = () => {
  const [loading, setLoading] = useState(false);
  const [predictions, setPredictions] = useState(null);
  const [timeHorizon, setTimeHorizon] = useState(24);
  const [minConfidence, setMinConfidence] = useState(0.6);

  const runPrediction = async () => {
    setLoading(true);
    try {
      const context = {
        recent_alerts: [],
        historical_events: [],
        current_environment: "production",
      };

      const result = await predictThreats(context, {
        timeHorizon,
        minConfidence,
        includeVulnForecast: true,
      });

      if (result.success !== false) {
        setPredictions(result);
      }
    } catch (error) {
      logger.error("Prediction failed:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="threat-prediction-widget">
      <div className="widget-header">
        <h3>🔮 Threat Prediction</h3>
        <span className="badge">FASE 8</span>
      </div>

      <div className="widget-controls">
        <div className="control-group">
          <label htmlFor="select-time-horizon-hours-0p33e">
            Time Horizon (hours)
          </label>
          <select
            id="select-time-horizon-hours-0p33e"
            value={timeHorizon}
            onChange={(e) => setTimeHorizon(Number(e.target.value))}
          >
            <option value={12}>12h</option>
            <option value={24}>24h</option>
            <option value={48}>48h</option>
            <option value={72}>72h</option>
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="select-min-confidence-bs8yn">Min Confidence</label>
          <select
            id="select-min-confidence-bs8yn"
            value={minConfidence}
            onChange={(e) => setMinConfidence(Number(e.target.value))}
          >
            <option value={0.5}>50%</option>
            <option value={0.6}>60%</option>
            <option value={0.7}>70%</option>
            <option value={0.8}>80%</option>
          </select>
        </div>

        <button
          className="predict-btn"
          onClick={runPrediction}
          disabled={loading}
        >
          {loading ? "⏳ Predicting..." : "🎯 Run Prediction"}
        </button>
      </div>

      {predictions && (
        <div className="predictions-results">
          <div className="result-section">
            <h4>Predicted Threats</h4>
            <div className="threat-list">
              {predictions.predicted_attacks?.length > 0 ? (
                predictions.predicted_attacks.map((attack, idx) => (
                  <div key={idx} className="threat-item">
                    <span className="threat-type">
                      {attack.type || "Unknown"}
                    </span>
                    <span className="confidence">
                      {Math.round((attack.confidence || 0) * 100)}%
                    </span>
                  </div>
                ))
              ) : (
                <p className="no-data">No threats predicted</p>
              )}
            </div>
          </div>

          <div className="result-section">
            <h4>Vulnerability Forecast</h4>
            <div className="vuln-list">
              {predictions.vuln_forecast?.length > 0 ? (
                predictions.vuln_forecast.map((vuln, idx) => (
                  <div key={idx} className="vuln-item">
                    <span className="vuln-id">{vuln.cve || "N/A"}</span>
                    <span className="exploit-prob">
                      {Math.round((vuln.exploit_probability || 0) * 100)}%
                    </span>
                  </div>
                ))
              ) : (
                <p className="no-data">No vulnerabilities forecasted</p>
              )}
            </div>
          </div>

          <div className="result-section">
            <h4>Hunting Recommendations</h4>
            <ul className="recommendations">
              {predictions.hunting_recommendations?.length > 0 ? (
                predictions.hunting_recommendations.map((rec, idx) => (
                  <li key={idx}>{rec}</li>
                ))
              ) : (
                <li className="no-data">No recommendations</li>
              )}
            </ul>
          </div>
        </div>
      )}

      {!predictions && !loading && (
        <div className="placeholder">
          <p>Configure parameters and run prediction to see future threats</p>
        </div>
      )}
    </div>
  );
};
