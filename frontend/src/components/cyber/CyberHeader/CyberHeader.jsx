import React from 'react';
import { Button } from '../../shared';
import { ModuleNav } from './components/ModuleNav';
import styles from './CyberHeader.module.css';

/**
 * CyberHeader - Header do módulo Cyber Security
 * Navegação entre módulos e status do sistema
 */
export const CyberHeader = ({
  currentTime,
  setCurrentView,
  activeModule,
  setActiveModule
}) => {
  return (
    <header className={styles.header}>
      {/* Top Bar */}
      <div className={styles.topBar}>
        <div className={styles.branding}>
          <div className={styles.logo}>
            <span>C</span>
          </div>
          <div className={styles.title}>
            <h1>CYBER SECURITY OPS</h1>
            <p>CENTRO DE OPERAÇÕES DIGITAIS</p>
          </div>
        </div>

        <div className={styles.actions}>
          <Button
            variant="success"
            size="sm"
            onClick={() => setCurrentView('operator')}
            icon="fas fa-arrow-left"
          >
            VOLTAR VÉRTICE
          </Button>

          <div className={styles.clock}>
            <div className={styles.time}>
              {currentTime.toLocaleTimeString()}
            </div>
            <div className={styles.date}>
              {currentTime.toLocaleDateString('pt-BR')}
            </div>
          </div>
        </div>
      </div>

      {/* Module Navigation */}
      <ModuleNav
        activeModule={activeModule}
        onModuleChange={setActiveModule}
      />
    </header>
  );
};

export default CyberHeader;
