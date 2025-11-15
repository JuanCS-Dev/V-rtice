/**
 * ═══════════════════════════════════════════════════════════════════════════
 * STATS SECTION - TACTICAL METRICS & COMBAT INTELLIGENCE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * MISSÃO: Métricas operacionais de guerra cibernética
 *
 * Capacidades:
 * - 4 painéis de inteligência tática
 * - Animação CountUp para contadores de eliminações
 * - Micro-interações de combate no hover
 * - Progress bars de capacidade operacional
 * - Borders com glow vermelho tático
 * - Tema Tactical Warfare
 * - Mobile-responsive
 */

import React, { useEffect, useState, useRef } from "react";
import styles from "./StatsSection.module.css";

export const StatsSection = ({ stats }) => {
  const statCards = [
    {
      id: "threats",
      icon: "🎯",
      label: "Alvos Identificados",
      value: stats.threatsDetected,
      trend: "+12%",
      trendUp: true,
      color: "danger",
      progress: 85,
    },
    {
      id: "monitoring",
      icon: "🔭",
      label: "Vigilância Ativa",
      value: stats.activeMonitoring,
      trend: "Operacional",
      trendUp: null,
      color: "info",
      progress: 95,
    },
    {
      id: "networks",
      icon: "🌐",
      label: "Redes Escaneadas",
      value: stats.networksScanned,
      trend: "+8%",
      trendUp: true,
      color: "success",
      progress: 78,
    },
    {
      id: "uptime",
      icon: "⚡",
      label: "Arsenal Online",
      value: stats.uptime,
      trend: "30 dias",
      trendUp: true,
      color: "warning",
      progress: 99,
    },
  ];

  return (
    <section className={styles.stats} aria-label="System statistics">
      <div className={styles.grid}>
        {statCards.map((stat, index) => (
          <StatCard key={stat.id} stat={stat} index={index} />
        ))}
      </div>
    </section>
  );
};

// Sub-component: Animated Stat Card
const StatCard = ({ stat, index }) => {
  const [count, setCount] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const cardRef = useRef(null);

  // Intersection Observer para animação quando entra na tela
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible(true);
          }
        });
      },
      { threshold: 0.1 },
    );

    const currentCard = cardRef.current;
    if (currentCard) {
      observer.observe(currentCard);
    }

    return () => {
      if (currentCard) {
        observer.unobserve(currentCard);
      }
    };
  }, []);

  // CountUp animation para números
  useEffect(() => {
    if (!isVisible) return;

    const target = typeof stat.value === "number" ? stat.value : 0;
    if (target === 0) return;

    const duration = 1500; // 1.5s
    const steps = 60;
    const increment = target / steps;
    let current = 0;

    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        setCount(target);
        clearInterval(timer);
      } else {
        setCount(Math.floor(current));
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [isVisible, stat.value]);

  const displayValue = typeof stat.value === "number" ? count : stat.value;

  return (
    <div
      ref={cardRef}
      className={`${styles.card} ${styles[stat.color]} ${isVisible ? styles.visible : ""}`}
      style={{ animationDelay: `${index * 0.1}s` }}
    >
      {/* Gradient Border Effect */}
      <div className={styles.borderGlow}></div>

      {/* Icon */}
      <div className={styles.icon}>{stat.icon}</div>

      {/* Content */}
      <div className={styles.content}>
        {/* Value - Animated Counter */}
        <div className={styles.value}>{displayValue}</div>

        {/* Label */}
        <div className={styles.label}>{stat.label}</div>

        {/* Progress Bar */}
        <div className={styles.progressBar}>
          <div
            className={styles.progressFill}
            style={{
              width: isVisible ? `${stat.progress}%` : "0%",
              transitionDelay: `${index * 0.1 + 0.3}s`,
            }}
          ></div>
        </div>

        {/* Trend */}
        <div
          className={`${styles.trend} ${stat.trendUp ? styles.trendUp : ""}`}
        >
          {stat.trendUp !== null && (
            <span className={styles.trendIcon}>{stat.trendUp ? "↑" : "↓"}</span>
          )}
          <span>{stat.trend}</span>
        </div>
      </div>

      {/* Hover Pulse Effect */}
      <div className={styles.pulse}></div>
    </div>
  );
};

export default StatsSection;
