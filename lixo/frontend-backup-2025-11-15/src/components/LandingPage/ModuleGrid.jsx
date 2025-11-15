/**
 * ModuleGrid - Grid de Módulos Disponíveis
 */

import React from "react";
import { useTranslation } from "react-i18next";
import { handleKeyboardClick } from "../../utils/accessibility";

export const ModuleGrid = ({ setCurrentView }) => {
  const { t } = useTranslation();

  const modules = [
    {
      id: "maximus",
      name: t("modules.maximus.name"),
      description: t("modules.maximus.description"),
      icon: "🧠",
      color: "gradient-ai",
      features: t("modules.maximus.features", { returnObjects: true }),
    },
    {
      id: "reactive-fabric",
      name: t("modules.reactive_fabric.name", "Reactive Fabric"),
      description: t(
        "modules.reactive_fabric.description",
        "Sistema de Deception e Honeypots com Inteligência em Tempo Real",
      ),
      icon: "🕸️",
      color: "red",
      features: t("modules.reactive_fabric.features", {
        returnObjects: true,
        defaultValue: [
          "Honeypot Monitoring",
          "Threat Intelligence",
          "Decoy Bayou Map",
          "Real-time Alerts",
        ],
      }),
    },
    {
      id: "hitl-console",
      name: t("modules.hitl_console.name", "HITL Console"),
      description: t(
        "modules.hitl_console.description",
        "Human-in-the-Loop Authorization para Respostas de Ameaças",
      ),
      icon: "🎯",
      color: "gradient-ai",
      features: t("modules.hitl_console.features", {
        returnObjects: true,
        defaultValue: [
          "Threat Review",
          "Decision Authorization",
          "Real-time Alerts",
          "Forensic Analysis",
        ],
      }),
    },
    {
      id: "defensive",
      name: t("modules.defensive.name"),
      description: t("modules.defensive.description"),
      icon: "🛡️",
      color: "cyan",
      features: t("modules.defensive.features", { returnObjects: true }),
    },
    {
      id: "offensive",
      name: t("modules.offensive.name"),
      description: t("modules.offensive.description"),
      icon: "⚔️",
      color: "red",
      features: t("modules.offensive.features", { returnObjects: true }),
    },
    {
      id: "purple",
      name: t("modules.purple.name"),
      description: t("modules.purple.description"),
      icon: "🟣",
      color: "purple",
      features: t("modules.purple.features", { returnObjects: true }),
    },
    {
      id: "cockpit",
      name: t("modules.cockpit.name", "Cockpit Soberano"),
      description: t(
        "modules.cockpit.description",
        "Centro de Comando & Inteligência",
      ),
      icon: "⚔️",
      color: "red",
      features: t("modules.cockpit.features", {
        returnObjects: true,
        defaultValue: [
          "Real-time Verdicts",
          "Alliance Graph",
          "C2L Commands",
          "Kill Switch",
        ],
      }),
    },
    {
      id: "osint",
      name: t("modules.osint.name"),
      description: t("modules.osint.description"),
      icon: "🕵️",
      color: "blue",
      features: t("modules.osint.features", { returnObjects: true }),
    },
    {
      id: "admin",
      name: t("modules.admin.name"),
      description: t("modules.admin.description"),
      icon: "⚙️",
      color: "yellow",
      features: t("modules.admin.features", { returnObjects: true }),
    },
  ];

  const handleModuleClick = (moduleId) => () => {
    setCurrentView(moduleId);
  };

  return (
    <div className="module-section">
      <h2 className="section-title">
        <span className="title-icon">⚡</span>
        {t("navigation.available_modules")}
      </h2>

      <div className="module-grid">
        {modules.map((module) => (
          <div
            key={module.id}
            className={`module-card module-${module.color}`}
            onClick={handleModuleClick(module.id)}
            onKeyDown={handleKeyboardClick(handleModuleClick(module.id))}
            role="button"
            tabIndex={0}
            aria-label={`${t("navigation.access_module")} ${module.name}`}
            data-testid={`nav-${module.id}-dashboard`}
          >
            <div className="module-header">
              <span className="module-icon" aria-hidden="true">
                {module.icon}
              </span>
              <h3 className="module-name">{module.name}</h3>
            </div>

            <p className="module-description">{module.description}</p>

            <div className="module-features">
              {module.features.map((feature, i) => (
                <span key={i} className="feature-tag">
                  {feature}
                </span>
              ))}
            </div>

            <div className="module-action">
              <span>{t("navigation.access_module").toUpperCase()}</span>
              <i className="fas fa-arrow-right" aria-hidden="true"></i>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
