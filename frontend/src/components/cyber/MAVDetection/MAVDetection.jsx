/**
 * MAV DETECTION - Manipulação e Amplificação Viralizada Detection
 *
 * Detecção de campanhas coordenadas de desinformação
 * Essencial para defesa democrática brasileira contra fake news e ataques coordenados
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <article> with data-maximus-tool="mav-detection"
 * - <header> for tool header
 * - <section> for metrics dashboard
 * - <section> for analysis form
 * - <section> for results display
 *
 * Maximus can:
 * - Identify tool via data-maximus-tool="mav-detection"
 * - Monitor analysis via data-maximus-status
 * - Access metrics via data-maximus-section="metrics"
 * - Interpret coordination signals via semantic structure
 *
 * Características:
 * - Análise de coordenação temporal, de conteúdo e de rede
 * - Detecção de astroturfing, desinformação e assédio em massa
 * - Suporte para Twitter, Facebook e Instagram
 * - Machine Learning para detecção de padrões coordenados
 *
 * Philosophy: Protege a democracia brasileira
 * i18n: react-i18next
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 * @version 2.0.0 (Maximus Vision)
 */

import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { getOffensiveService } from "@/services/offensive/OffensiveService";
import { formatDateTime } from "@/utils/dateHelpers";
import styles from "./MAVDetection.module.css";

export const MAVDetection = () => {
  const { t } = useTranslation();
  const offensiveService = getOffensiveService();

  const [posts, setPosts] = useState("[]");
  const [accounts, setAccounts] = useState("[]");
  const [platform, setPlatform] = useState("twitter");
  const [timeWindow, setTimeWindow] = useState("24h");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [metrics, setMetrics] = useState(null);

  // Load metrics on mount
  useEffect(() => {
    loadMetrics();
    const interval = setInterval(loadMetrics, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadMetrics = async () => {
    try {
      const response = await offensiveService.getMAVMetrics();
      if (response && response.success !== false) {
        setMetrics(response.data || response);
      }
    } catch (err) {
      logger.warn("[MAVDetection] Failed to load metrics:", err);
    }
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Parse JSON inputs with robust validation
      let parsedPosts;
      let parsedAccounts;

      try {
        parsedPosts = JSON.parse(posts);
        if (!Array.isArray(parsedPosts)) {
          throw new Error("Posts deve ser um array JSON");
        }
      } catch (jsonError) {
        throw new Error(`Erro ao parsear posts: ${jsonError.message}`);
      }

      try {
        parsedAccounts = JSON.parse(accounts);
        if (!Array.isArray(parsedAccounts)) {
          throw new Error("Accounts deve ser um array JSON");
        }
      } catch (jsonError) {
        throw new Error(`Erro ao parsear accounts: ${jsonError.message}`);
      }

      // Validate posts content
      if (parsedPosts.length === 0) {
        throw new Error(
          "É necessário fornecer pelo menos um post para análise",
        );
      }

      // Call MAV detection service
      const response = await offensiveService.detectMAVCampaign({
        posts: parsedPosts,
        accounts: parsedAccounts,
        platform,
        timeWindow,
      });

      if (response && response.success !== false) {
        setResult(response.data || response);
      } else {
        setError(response.error || "Falha ao detectar campanha MAV");
      }
    } catch (err) {
      setError(err.message || "Erro ao analisar campanha");
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toUpperCase()) {
      case "CRITICAL":
        return "#dc2626";
      case "HIGH":
        return "#ea580c";
      case "MEDIUM":
        return "#f59e0b";
      case "LOW":
        return "#10b981";
      default:
        return "#6b7280";
    }
  };

  const getCampaignTypeLabel = (type) => {
    const labels = {
      reputation_assassination: "🎯 Assassinato de Reputação",
      mass_harassment: "📢 Assédio em Massa",
      disinformation: "🚨 Desinformação",
      astroturfing: "🤖 Astroturfing",
    };
    return labels[type] || type;
  };

  const getPlatformIcon = (platform) => {
    const icons = {
      twitter: "🐦",
      facebook: "📘",
      instagram: "📷",
    };
    return icons[platform] || "🌐";
  };

  // Example data for quick testing
  const loadExampleData = () => {
    const examplePosts = [
      {
        id: "1",
        text: "Mensagem coordenada #1 sobre tema político",
        author: "user1",
        timestamp: new Date(Date.now() - 60000).toISOString(),
        engagement: { likes: 150, shares: 45 },
      },
      {
        id: "2",
        text: "Mensagem coordenada #1 sobre tema político",
        author: "user2",
        timestamp: new Date(Date.now() - 50000).toISOString(),
        engagement: { likes: 142, shares: 48 },
      },
      {
        id: "3",
        text: "Mensagem coordenada #1 sobre tema político",
        author: "user3",
        timestamp: new Date(Date.now() - 45000).toISOString(),
        engagement: { likes: 138, shares: 52 },
      },
    ];

    const exampleAccounts = [
      {
        id: "user1",
        created_at: new Date(Date.now() - 86400000 * 30).toISOString(),
        followers_count: 150,
        following_count: 2000,
        posts_count: 50,
      },
      {
        id: "user2",
        created_at: new Date(Date.now() - 86400000 * 28).toISOString(),
        followers_count: 142,
        following_count: 2100,
        posts_count: 48,
      },
      {
        id: "user3",
        created_at: new Date(Date.now() - 86400000 * 29).toISOString(),
        followers_count: 145,
        following_count: 1950,
        posts_count: 52,
      },
    ];

    setPosts(JSON.stringify(examplePosts, null, 2));
    setAccounts(JSON.stringify(exampleAccounts, null, 2));
  };

  return (
    <article
      className={styles.container}
      role="article"
      aria-labelledby="mav-detection-title"
      data-maximus-tool="mav-detection"
      data-maximus-category="defensive"
      data-maximus-status={loading ? "analyzing" : "ready"}
    >
      <header className={styles.header} data-maximus-section="tool-header">
        <h2 id="mav-detection-title">
          <span aria-hidden="true">🛡️🇧🇷</span>{" "}
          {t("defensive.mav.title", "MAV Detection")}
        </h2>
        <p className={styles.subtitle}>
          {t(
            "defensive.mav.subtitle",
            "Detecção de Manipulação e Amplificação Viralizada em redes sociais brasileiras",
          )}
        </p>
      </header>

      {/* Metrics Dashboard */}
      {metrics && (
        <section
          className={styles.metrics}
          role="region"
          aria-label="MAV detection metrics"
          data-maximus-section="metrics"
        >
          <div className={styles.metricCard}>
            <span className={styles.metricLabel}>Total Campanhas</span>
            <span className={styles.metricValue}>
              {metrics.total_campaigns || metrics.totalCampaigns || 0}
            </span>
          </div>
          <div className={styles.metricCard}>
            <span className={styles.metricLabel}>Ameaças Ativas</span>
            <span className={styles.metricValue}>
              {metrics.active_threats || metrics.activeThreats || 0}
            </span>
          </div>
          <div className={styles.metricCard}>
            <span className={styles.metricLabel}>Plataformas</span>
            <span className={styles.metricValue}>
              {metrics.platforms_monitored || metrics.platformsMonitored || 0}
            </span>
          </div>
          <div className={styles.metricCard}>
            <span className={styles.metricLabel}>Confiança Média</span>
            <span className={styles.metricValue}>
              {(
                (metrics.avg_confidence || metrics.avgConfidence || 0) * 100
              ).toFixed(1)}
              %
            </span>
          </div>
        </section>
      )}

      {/* Analysis Form */}
      <section
        role="region"
        aria-label="MAV campaign analysis form"
        data-maximus-section="form"
      >
        <form onSubmit={handleAnalyze} className={styles.form}>
          <div className={styles.formGroup}>
            <label htmlFor="posts">
              Posts (JSON Array)
              <button
                type="button"
                onClick={loadExampleData}
                className={styles.exampleBtn}
              >
                Carregar Exemplo
              </button>
            </label>
            <textarea
              id="posts"
              value={posts}
              onChange={(e) => setPosts(e.target.value)}
              placeholder='[{"id": "1", "text": "Post content", "author": "user1", "timestamp": "2024-01-01T00:00:00Z", "engagement": {"likes": 100, "shares": 50}}]'
              rows={8}
              required
              className={styles.textarea}
            />
            <span className={styles.hint}>
              Cada post deve ter: id, text, author, timestamp, engagement
              (likes, shares)
            </span>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="accounts">Accounts (JSON Array - Opcional)</label>
            <textarea
              id="accounts"
              value={accounts}
              onChange={(e) => setAccounts(e.target.value)}
              placeholder='[{"id": "user1", "created_at": "2023-01-01T00:00:00Z", "followers_count": 100, "following_count": 500, "posts_count": 50}]'
              rows={5}
              className={styles.textarea}
            />
            <span className={styles.hint}>
              Cada conta deve ter: id, created_at, followers_count,
              following_count, posts_count
            </span>
          </div>

          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label htmlFor="platform">Plataforma</label>
              <select
                id="platform"
                value={platform}
                onChange={(e) => setPlatform(e.target.value)}
                className={styles.select}
              >
                <option value="twitter">🐦 Twitter</option>
                <option value="facebook">📘 Facebook</option>
                <option value="instagram">📷 Instagram</option>
              </select>
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="timeWindow">Janela de Tempo</label>
              <select
                id="timeWindow"
                value={timeWindow}
                onChange={(e) => setTimeWindow(e.target.value)}
                className={styles.select}
              >
                <option value="1h">1 hora</option>
                <option value="6h">6 horas</option>
                <option value="24h">24 horas</option>
                <option value="7d">7 dias</option>
                <option value="30d">30 dias</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !posts.trim()}
            className={styles.submitBtn}
          >
            {loading ? "🔍 Analisando Campanha..." : "🔍 Detectar Campanha MAV"}
          </button>
        </form>
      </section>

      {/* Error Display */}
      {error && (
        <div className={styles.error}>
          <span className={styles.errorIcon}>⚠️</span>
          {error}
        </div>
      )}

      {/* Result Display */}
      {result && (
        <section
          className={styles.result}
          role="region"
          aria-label="MAV campaign detection results"
          data-maximus-section="results"
        >
          <div
            className={styles.resultHeader}
            style={{ borderLeftColor: getSeverityColor(result.severity) }}
          >
            <div>
              <h3>
                {result.is_mav_campaign || result.isMAVCampaign
                  ? "🚨 Campanha MAV Detectada"
                  : "✅ Sem Coordenação Detectada"}
              </h3>
              <span className={styles.campaignType}>
                {getCampaignTypeLabel(
                  result.campaign_type || result.campaignType,
                )}
              </span>
            </div>
            <span
              className={styles.severityBadge}
              style={{ backgroundColor: getSeverityColor(result.severity) }}
            >
              {(result.severity || "LOW").toUpperCase()}
            </span>
          </div>

          <div className={styles.resultContent}>
            {/* Campaign Overview */}
            <div className={styles.section}>
              <h4>📊 Visão Geral</h4>
              <div className={styles.resultRow}>
                <span className={styles.label}>Plataforma:</span>
                <span className={styles.value}>
                  {getPlatformIcon(result.platform || platform)}{" "}
                  {(result.platform || platform).toUpperCase()}
                </span>
              </div>
              <div className={styles.resultRow}>
                <span className={styles.label}>Confiança:</span>
                <span className={styles.value}>
                  {(
                    (result.confidence_score || result.confidenceScore || 0) *
                    100
                  ).toFixed(2)}
                  %
                </span>
              </div>
              <div className={styles.resultRow}>
                <span className={styles.label}>Posts Analisados:</span>
                <span className={styles.value}>
                  {result.posts_analyzed || result.postsAnalyzed || 0}
                </span>
              </div>
              <div className={styles.resultRow}>
                <span className={styles.label}>Contas Suspeitas:</span>
                <span className={styles.value}>
                  {result.suspicious_accounts?.length ||
                    result.suspiciousAccounts?.length ||
                    0}
                </span>
              </div>
            </div>

            {/* Coordination Signals */}
            {(result.coordination_signals || result.coordinationSignals) && (
              <div className={styles.section}>
                <h4>🎯 Sinais de Coordenação</h4>
                <div className={styles.coordinationGrid}>
                  {/* Temporal Coordination */}
                  <div className={styles.coordinationCard}>
                    <div className={styles.coordinationHeader}>
                      <span className={styles.coordinationIcon}>⏰</span>
                      <span className={styles.coordinationTitle}>
                        Coordenação Temporal
                      </span>
                    </div>
                    <div className={styles.coordinationScore}>
                      {(
                        (result.coordination_signals?.temporal ||
                          result.coordinationSignals?.temporal ||
                          0) * 100
                      ).toFixed(1)}
                      %
                    </div>
                    <p className={styles.coordinationDesc}>
                      Posts publicados em intervalos suspeitos
                    </p>
                  </div>

                  {/* Content Coordination */}
                  <div className={styles.coordinationCard}>
                    <div className={styles.coordinationHeader}>
                      <span className={styles.coordinationIcon}>📝</span>
                      <span className={styles.coordinationTitle}>
                        Similaridade de Conteúdo
                      </span>
                    </div>
                    <div className={styles.coordinationScore}>
                      {(
                        (result.coordination_signals?.content ||
                          result.coordinationSignals?.content ||
                          0) * 100
                      ).toFixed(1)}
                      %
                    </div>
                    <p className={styles.coordinationDesc}>
                      Conteúdo altamente similar entre posts
                    </p>
                  </div>

                  {/* Network Coordination */}
                  <div className={styles.coordinationCard}>
                    <div className={styles.coordinationHeader}>
                      <span className={styles.coordinationIcon}>🕸️</span>
                      <span className={styles.coordinationTitle}>
                        Coordenação de Rede
                      </span>
                    </div>
                    <div className={styles.coordinationScore}>
                      {(
                        (result.coordination_signals?.network ||
                          result.coordinationSignals?.network ||
                          0) * 100
                      ).toFixed(1)}
                      %
                    </div>
                    <p className={styles.coordinationDesc}>
                      Padrões suspeitos de conexão entre contas
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Detected Accounts */}
            {(result.suspicious_accounts?.length > 0 ||
              result.suspiciousAccounts?.length > 0) && (
              <div className={styles.section}>
                <h4>
                  👥 Contas Detectadas (
                  {
                    (result.suspicious_accounts || result.suspiciousAccounts)
                      .length
                  }
                  )
                </h4>
                <div className={styles.accountsList}>
                  {(result.suspicious_accounts || result.suspiciousAccounts)
                    .slice(0, 5)
                    .map((account, idx) => (
                      <div key={idx} className={styles.accountCard}>
                        <span className={styles.accountId}>
                          {account.account_id ||
                            account.accountId ||
                            account.id}
                        </span>
                        <span className={styles.accountScore}>
                          Score:{" "}
                          {(
                            (account.suspicion_score ||
                              account.suspicionScore ||
                              0) * 100
                          ).toFixed(1)}
                          %
                        </span>
                      </div>
                    ))}
                  {(result.suspicious_accounts || result.suspiciousAccounts)
                    .length > 5 && (
                    <div className={styles.accountMore}>
                      +
                      {(result.suspicious_accounts || result.suspiciousAccounts)
                        .length - 5}{" "}
                      mais...
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {(result.recommendations || result.mitigations) && (
              <div className={styles.section}>
                <h4>💡 Recomendações</h4>
                <ul className={styles.recommendationsList}>
                  {(result.recommendations || result.mitigations || []).map(
                    (rec, idx) => (
                      <li key={idx} className={styles.recommendationItem}>
                        {rec.action || rec}
                      </li>
                    ),
                  )}
                </ul>
              </div>
            )}

            {/* Timestamp */}
            <div className={styles.resultRow}>
              <span className={styles.label}>Análise realizada em:</span>
              <span className={styles.value}>
                {formatDateTime(result.timestamp || Date.now(), "N/A")}
              </span>
            </div>
          </div>
        </section>
      )}
    </article>
  );
};

export default MAVDetection;
