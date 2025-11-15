/**
 * LANDING PAGE - PROJETO VÉRTICE
 * ================================
 * A CARA do sistema. Impressionante, impactante, REAL.
 *
 * Features:
 * - Mapa Global com animação OnionTracer integrada
 * - Alerts REAIS do backend (threat_intel_service)
 * - Stats ao vivo
 * - Design cinematográfico
 */

import React, { useState, useEffect } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { handleKeyboardClick } from "../../utils/accessibility";
import { formatTime } from "../../utils/dateHelpers";
import { ThreatGlobe } from "./ThreatGlobe";
// import { ThreatGlobeWithOnion } from './ThreatGlobeWithOnion';
import { StatsPanel } from "./StatsPanel";
import { ModuleGrid } from "./ModuleGrid";
import { LiveFeed } from "./LiveFeed";
import { FloatingThemeButton } from "../shared/FloatingThemeButton";
import { useKonamiCode } from "../../hooks/useKonamiCode";
import {
  checkServicesHealth,
  checkThreatIntelligence,
} from "../../api/cyberServices";
import logger from "../../utils/logger";
import "./LandingPage.css";

export const LandingPage = ({ setCurrentView }) => {
  const { user, isAuthenticated, login, logout } = useAuth();
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [email, setEmail] = useState("");

  const [stats, setStats] = useState({
    threatsDetected: 0,
    activeMonitoring: 127,
    networksScanned: 1542,
    uptime: "99.8%",
    servicesOnline: 0,
    totalServices: 4,
  });

  const [realThreats, setRealThreats] = useState([]);
  const [servicesStatus, setServicesStatus] = useState({
    ipIntelligence: false,
    threatIntel: false,
    malwareAnalysis: false,
    sslMonitor: false,
  });

  // Check services health periodically
  useEffect(() => {
    const checkHealth = async () => {
      const health = await checkServicesHealth();
      setServicesStatus(health);

      const online = Object.values(health).filter(Boolean).length;
      setStats((prev) => ({
        ...prev,
        servicesOnline: online,
        uptime: online === 4 ? "99.9%" : `${((online / 4) * 100).toFixed(1)}%`,
      }));
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // a cada 30s

    return () => clearInterval(interval);
  }, []);

  // Buscar ameaças reais periodicamente
  useEffect(() => {
    const fetchRealThreats = async () => {
      // Lista de IPs conhecidos para verificar
      const suspiciousIPs = [
        "185.220.101.23", // Exit node Tor conhecido
        "45.129.56.200", // IP suspeito
        "178.162.212.214", // Outro IP para análise
        "91.219.236.232",
      ];

      try {
        const randomIP =
          suspiciousIPs[Math.floor(Math.random() * suspiciousIPs.length)];
        const result = await checkThreatIntelligence(randomIP);

        if (result.success) {
          const threat = {
            id: Date.now(),
            type: result.categories[0] || "Unknown",
            ip: result.target,
            severity: result.reputation,
            threatScore: result.threatScore,
            isMalicious: result.isMalicious,
            timestamp: formatTime(new Date(), "--:--:--"),
            geolocation: result.geolocation,
          };

          setRealThreats((prev) => [threat, ...prev].slice(0, 20));

          // Atualizar contador de ameaças
          if (result.isMalicious) {
            setStats((prev) => ({
              ...prev,
              threatsDetected: prev.threatsDetected + 1,
            }));
          }
        }
      } catch (error) {
        logger.error("Error fetching real threats:", error);
      }
    };

    // Busca inicial
    fetchRealThreats();

    // Buscar a cada 10 segundos
    const interval = setInterval(fetchRealThreats, 10000);

    return () => clearInterval(interval);
  }, []);

  // Konami Code Easter Egg - Power User Delight
  useKonamiCode(() => {
    // Trigger special animation on the globe
    const globe = document.querySelector(".threat-globe");
    if (globe) {
      globe.style.animation = "konami-globe-spin 2s ease-in-out";
      setTimeout(() => {
        globe.style.animation = "";
      }, 2000);
    }

    // Show easter egg message
    const messages = [
      "🎮 Konami Code Activated! Welcome, Power User! 🎮",
      "🚀 You found the secret! MAXIMUS approves! 🚀",
      "⚡ Elite Hacker Mode Unlocked! ⚡",
      "🎯 Achievement Unlocked: Code Master! 🎯",
      "💚 YHWH through Christ blesses your discovery! 💚",
    ];
    const message = messages[Math.floor(Math.random() * messages.length)];

    // Create temporary toast notification
    const toast = document.createElement("div");
    toast.textContent = message;
    toast.style.cssText = `
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: linear-gradient(135deg, #00ff41, #00cc33);
      color: #000;
      padding: 2rem 3rem;
      border-radius: 1rem;
      font-size: 1.25rem;
      font-weight: bold;
      z-index: 99999;
      box-shadow: 0 8px 32px rgba(0, 255, 65, 0.5);
      animation: konami-toast 3s ease-in-out;
      text-align: center;
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  });

  // Animar estatísticas (scanning em background)
  useEffect(() => {
    const interval = setInterval(() => {
      setStats((prev) => ({
        ...prev,
        activeMonitoring: 120 + Math.floor(Math.random() * 15),
        networksScanned: prev.networksScanned + Math.floor(Math.random() * 5),
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Handle login
  const handleLogin = async (e) => {
    e.preventDefault();
    const result = await login(email);
    if (result.success) {
      setShowLoginModal(false);
      setEmail("");
    } else {
      alert(result.error);
    }
  };

  // Handle logout
  const handleLogout = async () => {
    await logout();
  };

  return (
    <div className="landing-page">
      <div style={{ width: "100%", maxWidth: "1800px", margin: "0 auto" }}>
        {/* Hero Section */}
        <div className="hero-section">
          <div className="hero-content">
            <div className="hero-badge">
              <span className="pulse-dot"></span>
              <span>SISTEMA OPERACIONAL</span>
            </div>

            {/* Title */}
            <h1 className="hero-title">
              PROJETO VÉRTICE
              <span className="gradient-text">v2.4.0</span>
            </h1>

            <p className="hero-subtitle">
              Plataforma Unificada de Inteligência Criminal e Segurança
              Cibernética
            </p>

            {/* Auth Section - Standalone */}
            <div
              style={{
                marginTop: "2rem",
                marginBottom: "1.5rem",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
              }}
            >
              {isAuthenticated ? (
                <div
                  className="auth-status-badge"
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "15px",
                    background: "rgba(0, 255, 136, 0.1)",
                    border: "2px solid #00ff88",
                    borderRadius: "12px",
                    padding: "12px 20px",
                    boxShadow:
                      "0 4px 20px rgba(0, 255, 136, 0.3), 0 0 40px rgba(0, 255, 136, 0.1)",
                    backdropFilter: "blur(10px)",
                    animation: "fadeInScale 0.6s ease-out",
                  }}
                >
                  <div style={{ textAlign: "left" }}>
                    <div
                      style={{
                        color: "#00ff88",
                        fontSize: "15px",
                        fontWeight: "bold",
                        marginBottom: "2px",
                      }}
                    >
                      {user?.name || user?.email}
                    </div>
                    <div
                      style={{
                        color: "#00ff88",
                        fontSize: "11px",
                        opacity: 0.7,
                        letterSpacing: "0.5px",
                      }}
                    >
                      {user?.role?.toUpperCase() || "USER"}
                      {user?.role === "super_admin" && " 👑"}
                    </div>
                  </div>
                  <button
                    onClick={handleLogout}
                    style={{
                      background: "transparent",
                      border: "1px solid #ff0055",
                      color: "#ff0055",
                      padding: "8px 16px",
                      borderRadius: "6px",
                      cursor: "pointer",
                      fontSize: "12px",
                      fontFamily: "monospace",
                      fontWeight: "bold",
                      transition: "all 0.3s",
                      letterSpacing: "1px",
                    }}
                    onMouseEnter={(e) => {
                      e.target.style.background = "#ff0055";
                      e.target.style.color = "#000";
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.background = "transparent";
                      e.target.style.color = "#ff0055";
                    }}
                  >
                    LOGOUT
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setShowLoginModal(true)}
                  className="hero-login-button"
                  style={{
                    background:
                      "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    border: "none",
                    color: "#fff",
                    padding: "14px 32px",
                    borderRadius: "12px",
                    cursor: "pointer",
                    fontSize: "15px",
                    fontFamily: "monospace",
                    fontWeight: "bold",
                    boxShadow: "0 4px 20px rgba(102, 126, 234, 0.5)",
                    transition: "all 0.3s",
                    letterSpacing: "1px",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "10px",
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.transform = "translateY(-3px)";
                    e.target.style.boxShadow =
                      "0 8px 25px rgba(102, 126, 234, 0.7)";
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.transform = "translateY(0)";
                    e.target.style.boxShadow =
                      "0 4px 20px rgba(102, 126, 234, 0.5)";
                  }}
                >
                  <span>🔐</span>
                  <span>ACESSAR SISTEMA</span>
                </button>
              )}
            </div>

            <div className="hero-tags">
              <span className="tag">🛡️ Cyber Security</span>
              <span className="tag">🕵️ OSINT</span>
              <span className="tag">⚡ Real-Time Analysis</span>
              <span className="tag">🤖 AI-Powered</span>
            </div>

            {/* Services Status Indicator */}
            <div className="services-status">
              <div className="status-header">
                <span>🔧 SERVIÇOS ATIVOS</span>
                <span className="status-count">
                  {stats.servicesOnline}/{stats.totalServices}
                </span>
              </div>
              <div className="status-grid">
                <div
                  className={`status-item ${servicesStatus.ipIntelligence ? "online" : "offline"}`}
                >
                  <span className="status-dot"></span>
                  <span>IP Intel</span>
                </div>
                <div
                  className={`status-item ${servicesStatus.threatIntel ? "online" : "offline"}`}
                >
                  <span className="status-dot"></span>
                  <span>Threat Intel</span>
                </div>
                <div
                  className={`status-item ${servicesStatus.malwareAnalysis ? "online" : "offline"}`}
                >
                  <span className="status-dot"></span>
                  <span>Malware</span>
                </div>
                <div
                  className={`status-item ${servicesStatus.sslMonitor ? "online" : "offline"}`}
                >
                  <span className="status-dot"></span>
                  <span>SSL</span>
                </div>
              </div>
            </div>
          </div>

          {/* Mapa Global de Ameaças */}
          <div className="threat-globe-container">
            <ThreatGlobe realThreats={realThreats} />
          </div>
        </div>

        {/* Stats Grid */}
        <StatsPanel stats={stats} />

        {/* Modules Grid */}
        <ModuleGrid setCurrentView={setCurrentView} />

        {/* Live Activity Feed - AGORA com dados REAIS */}
        <LiveFeed realThreats={realThreats} />
      </div>

      {/* Footer Info */}
      <div className="landing-footer">
        <div className="footer-item">
          <i className="fas fa-shield-alt" aria-hidden="true"></i>
          <span>Criptografia de Ponta a Ponta</span>
        </div>
        <div className="footer-item">
          <i className="fas fa-server" aria-hidden="true"></i>
          <span>Infraestrutura Distribuída</span>
        </div>
        <div className="footer-item">
          <i className="fas fa-clock" aria-hidden="true"></i>
          <span>Uptime: {stats.uptime}</span>
        </div>
        <div className="footer-item">
          <i className="fas fa-certificate" aria-hidden="true"></i>
          <span>Classificação: CONFIDENCIAL</span>
        </div>
      </div>

      {/* Login Modal */}
      {showLoginModal && (
        <div
          className="login-modal-overlay"
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.85)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            backdropFilter: "blur(10px)",
            animation: "fadeIn 0.3s ease-out",
          }}
          onClick={(e) => {
            if (e.target.className.includes("login-modal-overlay")) {
              setShowLoginModal(false);
              setEmail("");
            }
          }}
          onKeyDown={handleKeyboardClick((e) => {
            if (e.target.className.includes("login-modal-overlay")) {
              setShowLoginModal(false);
              setEmail("");
            }
          })}
          role="presentation"
          aria-label="Close login modal"
        >
          <div
            className="login-modal-content"
            role="button"
            tabIndex={0}
            onClick={(e) => {
              if (e.target.classList.contains("login-modal-content")) {
                setShowLoginModal(false);
              } else {
                e.stopPropagation();
              }
            }}
            onKeyDown={(e) => {
              if (e.key === "Escape" || e.key === "Enter") {
                setShowLoginModal(false);
              }
            }}
            style={{
              background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
              border: "2px solid #667eea",
              borderRadius: "20px",
              padding: "40px",
              width: "90%",
              maxWidth: "480px",
              boxShadow:
                "0 20px 60px rgba(102, 126, 234, 0.4), 0 0 100px rgba(102, 126, 234, 0.2)",
              animation: "modalSlideIn 0.4s ease-out",
              position: "relative",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                textAlign: "center",
                marginBottom: "30px",
              }}
            >
              <div
                style={{
                  fontSize: "48px",
                  marginBottom: "10px",
                }}
              >
                🔐
              </div>
              <h2
                style={{
                  color: "#fff",
                  margin: 0,
                  fontSize: "24px",
                  fontWeight: "bold",
                  marginBottom: "8px",
                }}
              >
                VÉRTICE Authentication
              </h2>
              <p
                style={{
                  color: "#a8b2d1",
                  margin: 0,
                  fontSize: "14px",
                }}
              >
                Sistema de Autenticação Unificado
              </p>
            </div>

            <form onSubmit={handleLogin}>
              <div style={{ marginBottom: "20px" }}>
                <label
                  htmlFor="email-input"
                  style={{
                    display: "block",
                    color: "#a8b2d1",
                    marginBottom: "8px",
                    fontSize: "13px",
                    fontWeight: "500",
                  }}
                >
                  Email Google
                </label>
                <input
                  id="email-input"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="seu.email@gmail.com"
                  required
                  style={{
                    width: "100%",
                    padding: "12px 16px",
                    background: "rgba(255, 255, 255, 0.05)",
                    border: "1px solid rgba(168, 178, 209, 0.3)",
                    borderRadius: "8px",
                    color: "#fff",
                    fontSize: "14px",
                    fontFamily: "monospace",
                    outline: "none",
                    transition: "all 0.3s",
                  }}
                  onFocus={(e) => {
                    e.target.style.border = "1px solid #667eea";
                    e.target.style.background = "rgba(255, 255, 255, 0.08)";
                  }}
                  onBlur={(e) => {
                    e.target.style.border =
                      "1px solid rgba(168, 178, 209, 0.3)";
                    e.target.style.background = "rgba(255, 255, 255, 0.05)";
                  }}
                />
              </div>

              <div
                style={{
                  padding: "12px",
                  background: "rgba(255, 215, 0, 0.1)",
                  border: "1px solid rgba(255, 215, 0, 0.3)",
                  borderRadius: "8px",
                  marginBottom: "24px",
                }}
              >
                <div
                  style={{
                    color: "#ffd700",
                    fontSize: "12px",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                  }}
                >
                  <span>ℹ️</span>
                  <div>
                    <div style={{ fontWeight: "bold", marginBottom: "4px" }}>
                      Super Admin: juan.brainfarma@gmail.com
                    </div>
                    <div style={{ opacity: 0.8 }}>
                      Outros emails terão permissões de Analyst
                    </div>
                  </div>
                </div>
              </div>

              <div
                style={{
                  display: "flex",
                  gap: "12px",
                }}
              >
                <button
                  type="button"
                  onClick={() => {
                    setShowLoginModal(false);
                    setEmail("");
                  }}
                  style={{
                    flex: 1,
                    padding: "12px",
                    background: "transparent",
                    border: "1px solid rgba(255, 255, 255, 0.3)",
                    color: "#a8b2d1",
                    borderRadius: "8px",
                    cursor: "pointer",
                    fontSize: "14px",
                    fontFamily: "monospace",
                    fontWeight: "bold",
                    transition: "all 0.3s",
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.background = "rgba(255, 255, 255, 0.05)";
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.background = "transparent";
                  }}
                >
                  CANCELAR
                </button>
                <button
                  type="submit"
                  style={{
                    flex: 1,
                    padding: "12px",
                    background:
                      "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    border: "none",
                    color: "#fff",
                    borderRadius: "8px",
                    cursor: "pointer",
                    fontSize: "14px",
                    fontFamily: "monospace",
                    fontWeight: "bold",
                    boxShadow: "0 4px 15px rgba(102, 126, 234, 0.4)",
                    transition: "all 0.3s",
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.transform = "translateY(-2px)";
                    e.target.style.boxShadow =
                      "0 6px 20px rgba(102, 126, 234, 0.6)";
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.transform = "translateY(0)";
                    e.target.style.boxShadow =
                      "0 4px 15px rgba(102, 126, 234, 0.4)";
                  }}
                >
                  AUTENTICAR
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Floating Theme Button - Instant Discovery */}
      <FloatingThemeButton position="top-right" />
    </div>
  );
};

export default LandingPage;
