import React from "react";
import { Button } from "../../../shared";
import { formatTime } from "../../../../utils/dateHelpers";
import styles from "./SecurityHeader.module.css";

export const SecurityHeader = ({ lastUpdate, onRefresh }) => {
  return (
    <div className={styles.container}>
      <div className={styles.content}>
        <div className={styles.info}>
          <h2 className={styles.title}>SYSTEM SECURITY ANALYSIS</h2>
          <p className={styles.description}>
            Análise completa de segurança do sistema
          </p>
        </div>

        <Button
          variant="cyber"
          size="md"
          icon="fas fa-sync-alt"
          onClick={onRefresh}
        >
          ATUALIZAR DADOS
        </Button>
      </div>

      {lastUpdate && (
        <div className={styles.update}>
          Última atualização: {formatTime(lastUpdate, "--:--:--")}
        </div>
      )}
    </div>
  );
};

export default SecurityHeader;
