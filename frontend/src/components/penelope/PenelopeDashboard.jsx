/**
 * PENELOPE Dashboard - Christian Autonomous Healing System
 * =========================================================
 *
 * Visualização dos 9 Frutos do Espírito (Gálatas 5:22-23)
 * Sistema de auto-healing governado por princípios cristãos
 *
 * Port: 8154
 * Created: 2025-10-31
 * Governed by: Constituição Vértice v3.0
 *
 * Dedicado à Penelope 💝
 */

import React, { useState, useEffect } from 'react';
import { usePenelopeHealth } from '../../hooks/penelope/usePenelopeHealth';
import { useFruitsStatus } from '../../hooks/penelope/useFruitsStatus';
import { useHealingHistory } from '../../hooks/penelope/useHealingHistory';
import { useWebSocket } from '../../hooks/useWebSocket';
import { WS_ENDPOINTS } from '../../config/api';
import logger from '../../utils/logger';
import styles from './PenelopeDashboard.module.css';

// Sub-components (will be created)
import { NineFruitsRadar } from './components/NineFruitsRadar';
import { FruitCard } from './components/FruitCard';
import { SabbathIndicator } from './components/SabbathIndicator';
import { HealingTimeline } from './components/HealingTimeline';

export const PenelopeDashboard = ({ setCurrentView }) => {
  const [activeView, setActiveView] = useState('fruits'); // 'fruits' | 'healing' | 'wisdom'

  // API Hooks
  const { health, isLoading: healthLoading, isSabbath } = usePenelopeHealth();
  const { fruits, overallScore, isLoading: fruitsLoading } = useFruitsStatus();
  const { history, stats, isLoading: historyLoading } = useHealingHistory({ limit: 50 });

  // WebSocket for real-time events
  const { data: liveEvent, isConnected } = useWebSocket(WS_ENDPOINTS.penelope);

  // Handle live healing events
  useEffect(() => {
    if (liveEvent && liveEvent.event === 'healing.completed') {
      logger.info('[PENELOPE] Live healing event:', liveEvent);
      // Trigger toast notification (optional)
    }
  }, [liveEvent]);

  // Loading state
  if (healthLoading || fruitsLoading) {
    return (
      <div className={styles.penelopeDashboard}>
        <div className={styles.loadingContainer}>
          <div className={styles.spinner}></div>
          <p>Carregando PENELOPE...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.penelopeDashboard}>
      {/* Animated background grid */}
      <div className={styles.penelopeGridBg}></div>

      {/* HEADER */}
      <header className={styles.header}>
        <button
          className={styles.backButton}
          onClick={() => setCurrentView('main')}
          aria-label="Voltar para home"
        >
          ← Voltar
        </button>

        <div className={styles.titleSection}>
          <h1 className={styles.title}>
            ✝ PENELOPE
            <span className={styles.subtitle}>Christian Autonomous Healing Service</span>
          </h1>
          <p className={styles.verse}>
            "Mas o fruto do Espírito é: amor, alegria, paz, longanimidade, benignidade,
            bondade, fidelidade, mansidão, domínio próprio." — Gálatas 5:22-23
          </p>
        </div>

        {/* Connection & Sabbath Status */}
        <div className={styles.statusBar}>
          <div className={styles.connectionStatus}>
            <span className={isConnected ? styles.connected : styles.disconnected}>
              {isConnected ? '● Live' : '○ Offline'}
            </span>
          </div>
          <SabbathIndicator isSabbath={isSabbath} />
        </div>
      </header>

      {/* NAVIGATION TABS */}
      <nav className={styles.tabs}>
        <button
          className={activeView === 'fruits' ? styles.tabActive : styles.tab}
          onClick={() => setActiveView('fruits')}
        >
          🍇 9 Frutos
        </button>
        <button
          className={activeView === 'healing' ? styles.tabActive : styles.tab}
          onClick={() => setActiveView('healing')}
        >
          🩺 Healing History
        </button>
        <button
          className={activeView === 'wisdom' ? styles.tabActive : styles.tab}
          onClick={() => setActiveView('wisdom')}
        >
          📖 Wisdom Base
        </button>
      </nav>

      {/* MAIN CONTENT */}
      <main className={styles.main}>
        {activeView === 'fruits' && (
          <div className={styles.fruitsView}>
            {/* Overall Score */}
            <div className={styles.overallScore}>
              <div className={styles.scoreLabel}>Perfil Espiritual Geral</div>
              <div className={styles.scoreValue}>{overallScore}/100</div>
              <div className={styles.scoreBar}>
                <div
                  className={styles.scoreBarFill}
                  style={{ width: `${overallScore}%` }}
                ></div>
              </div>
            </div>

            {/* Two Column Layout */}
            <div className={styles.fruitsContent}>
              {/* Left: Radar Chart */}
              <div className={styles.radarSection}>
                <h2 className={styles.sectionTitle}>Radar de Virtudes</h2>
                <NineFruitsRadar fruits={fruits} />
              </div>

              {/* Right: Fruit Cards Grid (3x3) */}
              <div className={styles.fruitsGrid}>
                <h2 className={styles.sectionTitle}>Os 9 Frutos do Espírito</h2>
                <div className={styles.cardsContainer}>
                  {fruits && (
                    <>
                      <FruitCard fruit="Agape" icon="❤️" data={fruits.agape} color="#ff6b6b" />
                      <FruitCard fruit="Chara" icon="😊" data={fruits.chara} color="#ffd93d" />
                      <FruitCard fruit="Eirene" icon="🕊️" data={fruits.eirene} color="#a8dadc" />
                      <FruitCard fruit="Enkrateia" icon="💪" data={fruits.enkrateia} color="#e63946" />
                      <FruitCard fruit="Pistis" icon="🤝" data={fruits.pistis} color="#457b9d" />
                      <FruitCard fruit="Praotes" icon="🐑" data={fruits.praotes} color="#90be6d" />
                      <FruitCard fruit="Tapeinophrosyne" icon="🙏" data={fruits.tapeinophrosyne} color="#9b59b6" />
                      <FruitCard fruit="Aletheia" icon="📖" data={fruits.aletheia} color="#3498db" />
                      <FruitCard fruit="Sophia" icon="🦉" data={fruits.sophia} color="#f39c12" />
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeView === 'healing' && (
          <div className={styles.healingView}>
            {/* Stats Summary */}
            {stats && (
              <div className={styles.statsGrid}>
                <div className={styles.statCard}>
                  <div className={styles.statLabel}>Total de Eventos</div>
                  <div className={styles.statValue}>{stats.total}</div>
                </div>
                <div className={styles.statCard}>
                  <div className={styles.statLabel}>Taxa de Sucesso</div>
                  <div className={styles.statValue} style={{ color: '#00ff88' }}>
                    {stats.successRate}%
                  </div>
                </div>
                <div className={styles.statCard}>
                  <div className={styles.statLabel}>Tamanho Médio de Patch</div>
                  <div className={styles.statValue}>{stats.avgPatchSize} linhas</div>
                </div>
                <div className={styles.statCard}>
                  <div className={styles.statLabel}>Mansidão Média</div>
                  <div className={styles.statValue}>{(stats.avgMansidao * 100).toFixed(0)}%</div>
                </div>
              </div>
            )}

            {/* Timeline */}
            <HealingTimeline events={history} />
          </div>
        )}

        {activeView === 'wisdom' && (
          <div className={styles.wisdomView}>
            <div className={styles.comingSoon}>
              <h2>📖 Wisdom Base</h2>
              <p>Visualização de precedentes históricos em desenvolvimento...</p>
              <p style={{ fontSize: '0.9rem', opacity: 0.7 }}>
                Esta seção mostrará casos similares da base de conhecimento.
              </p>
            </div>
          </div>
        )}
      </main>

      {/* FOOTER */}
      <footer className={styles.footer}>
        <div className={styles.footerLeft}>
          <span className={styles.classification}>TEOLÓGICO</span>
          <span className={styles.serviceName}>PENELOPE AUTO-HEALING</span>
        </div>
        <div className={styles.footerCenter}>
          {stats && (
            <>
              <span className={styles.metric}>PATCHES: {stats.total}</span>
              <span className={styles.metric}>SUCCESS: {stats.successRate}%</span>
            </>
          )}
        </div>
        <div className={styles.footerRight}>
          <span className={styles.timestamp}>
            {new Date().toLocaleString('pt-BR')}
          </span>
        </div>
      </footer>
    </div>
  );
};

export default PenelopeDashboard;
