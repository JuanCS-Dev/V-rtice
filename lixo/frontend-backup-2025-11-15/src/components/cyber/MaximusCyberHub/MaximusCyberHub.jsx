/**
 * MAXIMUS CYBER HUB - AI-Powered Investigation Orchestration
 *
 * Hub de investigação AI com orquestração multi-serviço
 * Coordena análises de IP, domínio, vulnerabilidades e ameaças
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <article> with data-maximus-tool="maximus-cyber-hub"
 * - <header> for HubHeader component
 * - <section> for control panel (target input + services status)
 * - <section> for AI assistance (conditional)
 * - <section> for investigation timeline
 * - <section> for final report (conditional)
 *
 * Maximus can:
 * - Identify tool via data-maximus-tool="maximus-cyber-hub"
 * - Monitor investigation via data-maximus-status
 * - Access control panel via data-maximus-section="control-panel"
 * - Interpret investigation progress via semantic structure
 *
 * @version 2.0.0 (Maximus Vision)
 * @author Gemini + Maximus Vision Protocol
 * i18n: Ready for internationalization
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 */

import React from "react";
import AskMaximusButton from "../../shared/AskMaximusButton";
import { HubHeader } from "./components/HubHeader";
import { TargetInput } from "./components/TargetInput";
import { ServicesStatus } from "./components/ServicesStatus";
import { InvestigationInfo } from "./components/InvestigationInfo";
import { ExecutionTimeline } from "./components/ExecutionTimeline";
import { FinalReport } from "./components/FinalReport";
import { useMaximusHub } from "./hooks/useMaximusHub";
import styles from "./MaximusCyberHub.module.css";

export const MaximusCyberHub = () => {
  const {
    investigation,
    isAnalyzing,
    targetInput,
    setTargetInput,
    investigationType,
    setInvestigationType,
    analysisSteps,
    results,
    services,
    startInvestigation,
  } = useMaximusHub();

  return (
    <article
      className={styles.container}
      role="article"
      aria-labelledby="maximus-cyber-hub-title"
      data-maximus-tool="maximus-cyber-hub"
      data-maximus-category="shared"
      data-maximus-status={isAnalyzing ? "investigating" : "ready"}
    >
      <header
        role="region"
        aria-label="Hub header"
        data-maximus-section="header"
      >
        <h2 id="maximus-cyber-hub-title" className={styles.visuallyHidden}>
          Maximus Cyber Hub
        </h2>
        <HubHeader />
      </header>

      <div className={styles.content}>
        <section
          className={styles.controlPanel}
          role="region"
          aria-label="Investigation control panel"
          data-maximus-section="control-panel"
        >
          <TargetInput
            targetInput={targetInput}
            setTargetInput={setTargetInput}
            investigationType={investigationType}
            setInvestigationType={setInvestigationType}
            isAnalyzing={isAnalyzing}
            onStart={startInvestigation}
          />

          <ServicesStatus services={services} />
        </section>

        <div className={styles.timelinePanel}>
          {investigation && (
            <section
              style={{ marginBottom: "1rem" }}
              role="region"
              aria-label="AI assistance"
              data-maximus-section="ai-assistance"
            >
              <AskMaximusButton
                context={{
                  type: "ai_investigation",
                  data: investigation,
                  results,
                  services,
                  stepsCompleted: analysisSteps.filter(
                    (s) => s.status === "completed",
                  ).length,
                  totalSteps: analysisSteps.length,
                  investigationType,
                }}
                prompt="Analyze this AI investigation. What are the key findings, security risks, and recommended next steps?"
                size="medium"
                variant="secondary"
              />
            </section>
          )}

          <section
            role="region"
            aria-label="Investigation information"
            data-maximus-section="investigation-info"
          >
            <InvestigationInfo investigation={investigation} />
          </section>

          <section
            role="region"
            aria-label="Execution timeline"
            data-maximus-section="timeline"
          >
            <ExecutionTimeline analysisSteps={analysisSteps} />
          </section>

          {investigation && (
            <section
              role="region"
              aria-label="Investigation final report"
              data-maximus-section="final-report"
            >
              <FinalReport investigation={investigation} results={results} />
            </section>
          )}
        </div>
      </div>
    </article>
  );
};

export default MaximusCyberHub;
