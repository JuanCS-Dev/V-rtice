/**
 * ═══════════════════════════════════════════════════════════════════════════
 * LANDING PAGE - PROJETO VÉRTICE (REFATORADO NÍVEL PAGANI)
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Nova arquitetura:
 * - Design System com CSS Variables
 * - Componentes modulares em sections/
 * - Tema-agnóstico
 * - Mobile-first
 * - Performance otimizada
 *
 * Seções:
 * 1. Hero Section - Logo, Auth, Title, Globe
 * 2. Stats Section - Métricas animadas
 * 3. Modules Section - Cards premium
 * 4. Activity Feed - Timeline cinematográfico
 */

import React, { useState, useEffect } from "react";
import { formatTime } from "../../utils/dateHelpers";
import { useAuth } from "../../contexts/AuthContext";
import { useKonamiCode } from "../../hooks/useKonamiCode";
import {
  checkServicesHealth,
  checkThreatIntelligence,
} from "../../api/cyberServices";
import logger from "../../utils/logger";

// New modular sections
import { HeroSection } from "./sections/HeroSection";
import { StatsSection } from "./sections/StatsSection";
import { ModulesSection } from "./sections/ModulesSection";
import { ActivityFeedSection } from "./sections/ActivityFeedSection";

// Login Modal (keep from old version)
import { LoginModal } from "./components/LoginModal";

// Styles
import styles from "./LandingPage.module.css";

export const LandingPage = ({ setCurrentView }) => {
  const { user, isAuthenticated, login, logout } = useAuth();
  const [showLoginModal, setShowLoginModal] = useState(false);

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
    const interval = setInterval(checkHealth, 30000);

    return () => clearInterval(interval);
  }, []);

  // Fetch real threats periodically
  useEffect(() => {
    const fetchRealThreats = async () => {
      const suspiciousIPs = [
        "185.220.101.23", // Exit node Tor conhecido
        "45.129.56.200",
        "178.162.212.214",
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

    fetchRealThreats();
    const interval = setInterval(fetchRealThreats, 10000);

    return () => clearInterval(interval);
  }, []);

  // Animate stats (background scanning)
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

  // Konami Code Easter Egg
  useKonamiCode(() => {
    const messages = [
      "🎮 Konami Code Activated! Welcome, Power User! 🎮",
      "🚀 You found the secret! MAXIMUS approves! 🚀",
      "⚡ Elite Hacker Mode Unlocked! ⚡",
      "🎯 Achievement Unlocked: Code Master! 🎯",
      "💚 YHWH through Christ blesses your discovery! 💚",
    ];
    const message = messages[Math.floor(Math.random() * messages.length)];

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

  // Handlers
  const handleLogin = () => {
    setShowLoginModal(true);
  };

  const handleLogout = async () => {
    await logout();
  };

  const handleLoginSubmit = async (email) => {
    const result = await login(email);
    if (result.success) {
      setShowLoginModal(false);
    }
    return result;
  };

  return (
    <div className={styles.page}>
      {/* Hero Section - Logo, Auth, Title, Globe */}
      <HeroSection
        isAuthenticated={isAuthenticated}
        user={user}
        onLogin={handleLogin}
        onLogout={handleLogout}
        realThreats={realThreats}
        servicesStatus={servicesStatus}
        stats={stats}
      />

      {/* Stats Section - Animated Metrics */}
      <StatsSection stats={stats} />

      {/* Modules Section - Premium Cards */}
      <ModulesSection setCurrentView={setCurrentView} />

      {/* Activity Feed - Cinematographic Timeline */}
      <ActivityFeedSection realThreats={realThreats} />

      {/* Footer Info */}
      <footer className={styles.footer}>
        <div className={styles.footerItem}>
          <i className="fas fa-shield-alt" aria-hidden="true"></i>
          <span>Criptografia de Ponta a Ponta</span>
        </div>
        <div className={styles.footerItem}>
          <i className="fas fa-server" aria-hidden="true"></i>
          <span>Infraestrutura Distribuída</span>
        </div>
        <div className={styles.footerItem}>
          <i className="fas fa-clock" aria-hidden="true"></i>
          <span>Uptime: {stats.uptime}</span>
        </div>
        <div className={styles.footerItem}>
          <i className="fas fa-certificate" aria-hidden="true"></i>
          <span>Classificação: CONFIDENCIAL</span>
        </div>
      </footer>

      {/* Login Modal */}
      {showLoginModal && (
        <LoginModal
          onClose={() => setShowLoginModal(false)}
          onSubmit={handleLoginSubmit}
        />
      )}
    </div>
  );
};

export default LandingPage;
