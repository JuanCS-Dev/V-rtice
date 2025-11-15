/**
 * CommandConsole - Sovereign C2L Command Interface
 *
 * @version 1.0.0
 */

import React, { useState } from "react";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import { formatTime } from "@/utils/dateHelpers";
import { useCommandBus } from "../../hooks/useCommandBus";
import styles from "./CommandConsole.module.css";

const COMMAND_TYPES = [
  {
    id: "MUTE",
    label: "MUTE",
    icon: "🔇",
    description: "Silenciar agente temporariamente",
    severity: "low",
  },
  {
    id: "ISOLATE",
    label: "ISOLATE",
    icon: "🚧",
    description: "Isolar agente da rede",
    severity: "medium",
  },
  {
    id: "TERMINATE",
    label: "TERMINATE",
    icon: "☠️",
    description: "Terminar agente permanentemente",
    severity: "critical",
  },
];

export const CommandConsole = ({ availableAgents = [] }) => {
  const { t } = useTranslation();
  const { sendCommand, loading, error, lastCommand } = useCommandBus();

  const [selectedCommand, setSelectedCommand] = useState(null);
  const [selectedAgents, setSelectedAgents] = useState([]);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [muteDuration, setMuteDuration] = useState(300);

  const handleAgentToggle = (agentId) => {
    setSelectedAgents((prev) =>
      prev.includes(agentId)
        ? prev.filter((id) => id !== agentId)
        : [...prev, agentId],
    );
  };

  const handleCommandSelect = (commandType) => {
    setSelectedCommand(commandType);
    if (commandType === "TERMINATE") {
      setConfirmDialogOpen(true);
    }
  };

  const executeCommand = async () => {
    if (!selectedCommand || selectedAgents.length === 0) return;

    try {
      const params =
        selectedCommand === "MUTE" ? { duration_seconds: muteDuration } : {};

      await sendCommand(selectedCommand, selectedAgents, params);

      setSelectedCommand(null);
      setSelectedAgents([]);
      setConfirmDialogOpen(false);
    } catch (err) {
      logger.error("[CommandConsole] Command failed:", err);
    }
  };

  const canExecute = selectedCommand && selectedAgents.length > 0 && !loading;

  return (
    <div className={styles.commandConsole}>
      <div className={styles.consoleHeader}>
        <h3>
          <span className={styles.headerIcon}>⚡</span>
          {t("cockpit.commands.title", "Console de Comando")}
        </h3>
        {lastCommand && (
          <div className={styles.lastCommandStatus}>
            <span className={styles.statusDot}></span>
            Último: {lastCommand.type} ({formatTime(lastCommand.timestamp)})
          </div>
        )}
      </div>

      {error && (
        <div className={styles.errorBanner}>
          <span>⚠️</span>
          {error}
        </div>
      )}

      <div className={styles.commandSelector}>
        <label className={styles.sectionLabel}>
          {t("cockpit.commands.selectCommand", "Selecionar Comando")}
        </label>
        <div className={styles.commandGrid}>
          {COMMAND_TYPES.map((cmd) => (
            <button
              key={cmd.id}
              className={`${styles.commandButton} ${styles[`severity-${cmd.severity}`]} ${selectedCommand === cmd.id ? styles.selected : ""}`}
              onClick={() => handleCommandSelect(cmd.id)}
              disabled={loading}
            >
              <span className={styles.commandIcon}>{cmd.icon}</span>
              <span className={styles.commandLabel}>{cmd.label}</span>
              <small className={styles.commandDesc}>{cmd.description}</small>
            </button>
          ))}
        </div>
      </div>

      {selectedCommand === "MUTE" && (
        <div className={styles.parameterSection}>
          <label className={styles.sectionLabel}>Duração (segundos)</label>
          <input
            type="number"
            value={muteDuration}
            onChange={(e) => setMuteDuration(parseInt(e.target.value))}
            min={60}
            max={3600}
            className={styles.parameterInput}
          />
        </div>
      )}

      <div className={styles.agentSelector}>
        <label className={styles.sectionLabel}>
          {t("cockpit.commands.selectAgents", "Selecionar Agentes")} (
          {selectedAgents.length})
        </label>
        <div className={styles.agentList}>
          {availableAgents.length === 0 ? (
            <div className={styles.emptyState}>
              {t("cockpit.commands.noAgents", "Nenhum agente disponível")}
            </div>
          ) : (
            availableAgents.map((agent) => (
              <div
                key={agent.id}
                className={`${styles.agentItem} ${selectedAgents.includes(agent.id) ? styles.selected : ""}`}
                onClick={() => handleAgentToggle(agent.id)}
              >
                <input
                  type="checkbox"
                  checked={selectedAgents.includes(agent.id)}
                  onChange={() => {}}
                  className={styles.agentCheckbox}
                />
                <div className={styles.agentInfo}>
                  <span className={styles.agentName}>
                    {agent.name || agent.id}
                  </span>
                  <span className={styles.agentStatus}>
                    {agent.status || "ACTIVE"}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className={styles.consoleFooter}>
        <button
          className={styles.executeButton}
          onClick={executeCommand}
          disabled={!canExecute}
        >
          {loading ? (
            <>
              <span className={styles.spinner}></span>
              {t("common.executing", "Executando")}...
            </>
          ) : (
            <>
              <span>⚡</span>
              {t("cockpit.commands.execute", "Executar Comando")}
            </>
          )}
        </button>
      </div>

      {confirmDialogOpen && selectedCommand === "TERMINATE" && (
        <div className={styles.confirmDialog}>
          <div className={styles.dialogContent}>
            <div className={styles.dialogHeader}>
              <span className={styles.warningIcon}>⚠️</span>
              <h3>
                {t("cockpit.commands.confirmTerminate", "Confirmar Terminação")}
              </h3>
            </div>
            <p className={styles.dialogText}>
              Você está prestes a <strong>TERMINAR</strong>{" "}
              {selectedAgents.length} agente(s). Esta ação é{" "}
              <strong>IRREVERSÍVEL</strong>.
            </p>
            <div className={styles.dialogActions}>
              <button
                className={styles.cancelButton}
                onClick={() => {
                  setConfirmDialogOpen(false);
                  setSelectedCommand(null);
                }}
              >
                {t("common.cancel", "Cancelar")}
              </button>
              <button className={styles.confirmButton} onClick={executeCommand}>
                {t("cockpit.commands.confirmAction", "Confirmar Terminação")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

CommandConsole.propTypes = {
  availableAgents: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      name: PropTypes.string,
      status: PropTypes.string,
    }),
  ),
};

// defaultProps migrated to default parameters (React 18 compatible)
