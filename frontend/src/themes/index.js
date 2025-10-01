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
    icon: '🟢'
  },
  {
    id: 'cyber-blue',
    name: 'Cyber Blue',
    description: 'Azul cibernético futurista',
    primary: '#00d4ff',
    icon: '🔵'
  },
  {
    id: 'purple-haze',
    name: 'Purple Haze',
    description: 'Roxo neon vibrante',
    primary: '#c77dff',
    icon: '🟣'
  },
  {
    id: 'amber-alert',
    name: 'Amber Alert',
    description: 'Âmbar de alerta operacional',
    primary: '#ffb703',
    icon: '🟠'
  },
  {
    id: 'red-alert',
    name: 'Red Alert',
    description: 'Vermelho de alerta crítico',
    primary: '#ff0a54',
    icon: '🔴'
  },
  {
    id: 'stealth-mode',
    name: 'Stealth Mode',
    description: 'Modo furtivo discreto',
    primary: '#8b8b8b',
    icon: '⚫'
  },
  {
    id: 'windows11',
    name: 'Windows 11',
    description: 'Clean, sóbrio e profissional',
    primary: '#0078d4',
    icon: '🪟'
  }
];

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
