import React from 'react';
import styles from './ModuleNav.module.css';

const MODULES = [
  { id: 'overview', name: 'OVERVIEW', icon: '🛡️' },
  { id: 'aurora', name: 'MAXIMUS AI HUB', icon: '🤖', isAI: true },
  { id: 'exploits', name: 'CVE EXPLOITS', icon: '🐛', isWorldClass: true },
  { id: 'domain', name: 'DOMAIN INTEL', icon: '🌐' },
  { id: 'ip', name: 'IP ANALYSIS', icon: '🎯' },
  { id: 'network', name: 'NET MONITOR', icon: '📡' },
  { id: 'nmap', name: 'NMAP SCAN', icon: '⚡' },
  { id: 'threats', name: 'THREAT MAP', icon: '🗺️' },
  { id: 'vulnscan', name: 'VULN SCANNER', icon: '💥', isOffensive: true },
  { id: 'socialeng', name: 'SOCIAL ENG', icon: '🎭', isOffensive: true }
];

export const ModuleNav = ({ activeModule, onModuleChange }) => {
  const getModuleClass = (module, isActive) => {
    const classes = [styles.module];

    if (isActive) {
      classes.push(styles.moduleActive);
      if (module.isAI) classes.push(styles.moduleAI);
      else if (module.isWorldClass) classes.push(styles.moduleWorldClass);
      else if (module.isOffensive) classes.push(styles.moduleOffensive);
      else classes.push(styles.moduleCyber);
    } else {
      classes.push(styles.moduleInactive);
      if (module.isAI) classes.push(styles.moduleAIInactive);
      else if (module.isWorldClass) classes.push(styles.moduleWorldClassInactive);
      else if (module.isOffensive) classes.push(styles.moduleOffensiveInactive);
    }

    return classes.join(' ');
  };

  return (
    <nav className={styles.container}>
      <div className={styles.modules}>
        {MODULES.map((module) => (
          <button
            key={module.id}
            onClick={() => onModuleChange(module.id)}
            className={getModuleClass(module, activeModule === module.id)}
          >
            <span className={styles.icon}>{module.icon}</span>
            {module.name}
            {module.isOffensive && <span className={styles.badge}>⚠️</span>}
            {module.isWorldClass && <span className={styles.badge}>⭐</span>}
          </button>
        ))}
      </div>
    </nav>
  );
};

export default ModuleNav;
