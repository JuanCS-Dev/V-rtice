/**
 * NavigationTimeline - Timeline de Navegações
 * ============================================
 *
 * Exibe histórico cronológico de todas as navegações realizadas
 * pelo MABA browser agent.
 */

import React, { useMemo, useState } from "react";
import styles from "./NavigationTimeline.module.css";

export const NavigationTimeline = ({ sessions, isLoading }) => {
  const [filter, setFilter] = useState("all"); // all, success, error

  // Extract all navigations from sessions and sort by timestamp
  const navigations = useMemo(() => {
    if (!sessions || sessions.length === 0) return [];

    const allNavs = sessions.flatMap((session) =>
      (session.navigations || []).map((nav) => ({
        ...nav,
        sessionId: session.session_id,
        sessionUrl: session.current_url,
      })),
    );

    // Sort by timestamp desc (newest first)
    return allNavs.sort(
      (a, b) => new Date(b.timestamp) - new Date(a.timestamp),
    );
  }, [sessions]);

  // Apply filter
  const filteredNavigations = useMemo(() => {
    if (filter === "all") return navigations;
    if (filter === "success") return navigations.filter((n) => n.success);
    if (filter === "error") return navigations.filter((n) => !n.success);
    return navigations;
  }, [navigations, filter]);

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  const getNavigationType = (nav) => {
    if (nav.action === "click")
      return { icon: "👆", label: "Click", color: "blue" };
    if (nav.action === "navigate")
      return { icon: "🧭", label: "Navigate", color: "green" };
    if (nav.action === "type")
      return { icon: "⌨️", label: "Type", color: "purple" };
    if (nav.action === "screenshot")
      return { icon: "📸", label: "Screenshot", color: "yellow" };
    return { icon: "🔄", label: "Action", color: "gray" };
  };

  if (isLoading) {
    return (
      <div className={styles.loading}>
        <div className={styles.spinner}></div>
        <p>Carregando timeline...</p>
      </div>
    );
  }

  if (!sessions || sessions.length === 0) {
    return (
      <div className={styles.empty}>
        <p>📜 Nenhuma navegação registrada ainda</p>
        <p className={styles.emptyHint}>
          Crie uma sessão de browser para ver o histórico
        </p>
      </div>
    );
  }

  return (
    <div className={styles.timeline}>
      {/* Header with filters */}
      <div className={styles.header}>
        <h3 className={styles.title}>
          📜 Timeline de Navegações ({filteredNavigations.length})
        </h3>

        <div className={styles.filters}>
          <button
            className={`${styles.filter} ${filter === "all" ? styles.active : ""}`}
            onClick={() => setFilter("all")}
          >
            Todas
          </button>
          <button
            className={`${styles.filter} ${filter === "success" ? styles.active : ""}`}
            onClick={() => setFilter("success")}
          >
            ✅ Sucesso
          </button>
          <button
            className={`${styles.filter} ${filter === "error" ? styles.active : ""}`}
            onClick={() => setFilter("error")}
          >
            ❌ Erros
          </button>
        </div>
      </div>

      {/* Timeline Items */}
      {filteredNavigations.length === 0 ? (
        <div className={styles.empty}>
          <p>🔍 Nenhuma navegação encontrada com esse filtro</p>
        </div>
      ) : (
        <div className={styles.items}>
          {filteredNavigations.map((nav, index) => {
            const type = getNavigationType(nav);

            return (
              <div
                key={`${nav.sessionId}-${nav.timestamp}-${index}`}
                className={`${styles.item} ${nav.success ? styles.success : styles.error}`}
              >
                {/* Timeline connector */}
                <div className={styles.connector}>
                  <div className={styles.dot}></div>
                  {index < filteredNavigations.length - 1 && (
                    <div className={styles.line}></div>
                  )}
                </div>

                {/* Content */}
                <div className={styles.content}>
                  {/* Header */}
                  <div className={styles.itemHeader}>
                    <div className={styles.typeInfo}>
                      <span
                        className={`${styles.typeIcon} ${styles[type.color]}`}
                      >
                        {type.icon}
                      </span>
                      <span className={styles.typeLabel}>{type.label}</span>
                    </div>

                    <div className={styles.timestamp}>
                      {formatTimestamp(nav.timestamp)}
                    </div>
                  </div>

                  {/* Body */}
                  <div className={styles.itemBody}>
                    {nav.url && (
                      <div className={styles.url}>
                        <span className={styles.urlIcon}>🔗</span>
                        <span className={styles.urlText}>{nav.url}</span>
                      </div>
                    )}

                    {nav.target && (
                      <div className={styles.target}>
                        <span className={styles.targetLabel}>Target:</span>
                        <code className={styles.targetCode}>{nav.target}</code>
                      </div>
                    )}

                    {nav.value && (
                      <div className={styles.value}>
                        <span className={styles.valueLabel}>Value:</span>
                        <code className={styles.valueCode}>{nav.value}</code>
                      </div>
                    )}

                    {/* Session info */}
                    <div className={styles.sessionInfo}>
                      <span className={styles.sessionLabel}>
                        Session #{nav.sessionId}
                      </span>
                      {nav.sessionUrl && (
                        <span className={styles.sessionUrl}>
                          {nav.sessionUrl}
                        </span>
                      )}
                    </div>

                    {/* Status indicator */}
                    <div className={styles.status}>
                      {nav.success ? (
                        <span className={styles.statusSuccess}>✅ Sucesso</span>
                      ) : (
                        <span className={styles.statusError}>
                          ❌ Erro: {nav.error || "Unknown error"}
                        </span>
                      )}
                    </div>

                    {/* Additional metrics */}
                    {nav.duration && (
                      <div className={styles.duration}>
                        ⏱️ Duração: {nav.duration}ms
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default NavigationTimeline;
