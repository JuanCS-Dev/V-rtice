/**
 * BrowserSessionManager - Gerenciador de Sessões de Browser
 * ===========================================================
 *
 * Lista e gerencia sessões ativas do MABA browser agent.
 * Permite criar novas sessões e fechar existentes.
 */

import React, { useState } from "react";
import { formatDateTime } from "../../../utils/dateHelpers";
import styles from "./BrowserSessionManager.module.css";

export const BrowserSessionManager = ({
  sessions,
  isLoading,
  onCreateSession,
  onCloseSession,
}) => {
  const [newUrl, setNewUrl] = useState("");
  const [creating, setCreating] = useState(false);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newUrl.trim()) return;

    setCreating(true);
    try {
      await onCreateSession(newUrl);
      setNewUrl("");
    } finally {
      setCreating(false);
    }
  };

  const handleClose = async (sessionId) => {
    if (!confirm("Fechar esta sessão?")) return;
    await onCloseSession(sessionId);
  };

  const formatTimestamp = (timestamp) => {
    return formatDateTime(timestamp, "N/A");
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "active":
        return "green";
      case "idle":
        return "yellow";
      case "error":
        return "red";
      default:
        return "gray";
    }
  };

  return (
    <div className={styles.manager}>
      {/* Create New Session Form */}
      <div className={styles.createSection}>
        <h3 className={styles.sectionTitle}>🚀 Nova Sessão de Browser</h3>
        <form className={styles.form} onSubmit={handleCreate}>
          <input
            type="url"
            className={styles.input}
            placeholder="https://example.com"
            value={newUrl}
            onChange={(e) => setNewUrl(e.target.value)}
            disabled={creating}
            required
          />
          <button
            type="submit"
            className={styles.createButton}
            disabled={creating || !newUrl.trim()}
          >
            {creating ? "⏳ Criando..." : "➕ Criar Sessão"}
          </button>
        </form>
      </div>

      {/* Active Sessions List */}
      <div className={styles.sessionsSection}>
        <h3 className={styles.sectionTitle}>
          🌐 Sessões Ativas ({sessions?.length || 0})
        </h3>

        {isLoading && (
          <div className={styles.loading}>
            <div className={styles.spinner}></div>
            <p>Carregando sessões...</p>
          </div>
        )}

        {!isLoading && (!sessions || sessions.length === 0) && (
          <div className={styles.empty}>
            <p>📭 Nenhuma sessão ativa</p>
            <p className={styles.emptyHint}>
              Crie uma nova sessão acima para começar
            </p>
          </div>
        )}

        {!isLoading && sessions && sessions.length > 0 && (
          <div className={styles.sessionsList}>
            {sessions.map((session) => (
              <div key={session.session_id} className={styles.session}>
                {/* Header */}
                <div className={styles.sessionHeader}>
                  <div className={styles.sessionInfo}>
                    <div className={styles.sessionId}>
                      Session #{session.session_id}
                    </div>
                    <div className={styles.sessionUrl}>
                      <span className={styles.urlIcon}>🔗</span>
                      <span className={styles.urlText}>
                        {session.current_url}
                      </span>
                    </div>
                  </div>
                  <div className={styles.sessionActions}>
                    <span
                      className={`${styles.status} ${styles[getStatusColor(session.status)]}`}
                    >
                      {session.status}
                    </span>
                    <button
                      className={styles.closeButton}
                      onClick={() => handleClose(session.session_id)}
                      aria-label="Fechar sessão"
                    >
                      ✕
                    </button>
                  </div>
                </div>

                {/* Metrics */}
                <div className={styles.sessionMetrics}>
                  <div className={styles.metric}>
                    <span className={styles.metricLabel}>Páginas:</span>
                    <span className={styles.metricValue}>
                      {session.pages_visited || 0}
                    </span>
                  </div>
                  <div className={styles.metric}>
                    <span className={styles.metricLabel}>Elementos:</span>
                    <span className={styles.metricValue}>
                      {session.elements_learned || 0}
                    </span>
                  </div>
                  <div className={styles.metric}>
                    <span className={styles.metricLabel}>Screenshots:</span>
                    <span className={styles.metricValue}>
                      {session.screenshots || 0}
                    </span>
                  </div>
                  <div className={styles.metric}>
                    <span className={styles.metricLabel}>Criado:</span>
                    <span className={styles.metricValue}>
                      {formatTimestamp(session.created_at)}
                    </span>
                  </div>
                </div>

                {/* Last Navigation */}
                {session.last_navigation && (
                  <div className={styles.lastNavigation}>
                    <span className={styles.navIcon}>🧭</span>
                    <span className={styles.navText}>
                      Última navegação: {session.last_navigation}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default BrowserSessionManager;
