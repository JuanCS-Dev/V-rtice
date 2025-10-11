// Importação de todos os temas disponíveis
import './default.css';
import './cyber-blue.css';
import './purple-haze.css';
import './amber-alert.css';
import './red-alert.css';
import './stealth-mode.css';
import './windows11.css';

// Metadados dos temas para o seletor
export const themes = [
  {
    id: 'default',
    name: 'Matrix Green',
    description: 'Tema clássico inspirado em Matrix',
    primary: '#00ff41',
    icon: '🟢',
    category: 'hacker'
  },
  {
    id: 'cyber-blue',
    name: 'Cyber Blue',
    description: 'Azul cibernético futurista',
    primary: '#00d4ff',
    icon: '🔵',
    category: 'hacker'
  },
  {
    id: 'purple-haze',
    name: 'Purple Haze',
    description: 'Roxo neon vibrante',
    primary: '#c77dff',
    icon: '🟣',
    category: 'hacker'
  },
  {
    id: 'amber-alert',
    name: 'Amber Alert',
    description: 'Âmbar de alerta operacional',
    primary: '#ffb703',
    icon: '🟠',
    category: 'operational'
  },
  {
    id: 'red-alert',
    name: 'Red Alert',
    description: 'Vermelho de alerta crítico',
    primary: '#ff0a54',
    icon: '🔴',
    category: 'operational'
  },
  {
    id: 'stealth-mode',
    name: 'Stealth Mode',
    description: 'Modo furtivo discreto',
    primary: '#8b8b8b',
    icon: '⚫',
    category: 'operational'
  },
  {
    id: 'windows11',
    name: 'Windows 11',
    description: 'Clean, sóbrio e profissional',
    primary: '#0078d4',
    icon: '🪟',
    category: 'enterprise'
  }
];

// Theme categories metadata
export const themeCategories = {
  hacker: {
    id: 'hacker',
    name: 'Hacker Themes',
    icon: '🔥',
    description: 'Matrix-inspired cyberpunk aesthetics'
  },
  enterprise: {
    id: 'enterprise',
    name: 'Enterprise Themes',
    icon: '💼',
    description: 'Professional, clean, corporate design'
  },
  operational: {
    id: 'operational',
    name: 'Operational Themes',
    icon: '⚠️',
    description: 'Alert and stealth modes for operations'
  }
};

// Função para aplicar o tema
export const applyTheme = (themeId) => {
  document.documentElement.setAttribute('data-theme', themeId);
  localStorage.setItem('vertice-theme', themeId);
};

// Função para obter o tema atual
export const getCurrentTheme = () => {
  return localStorage.getItem('vertice-theme') || 'default';
};

// Função para inicializar o tema salvo
export const initializeTheme = () => {
  const savedTheme = getCurrentTheme();
  applyTheme(savedTheme);
  return savedTheme;
};
