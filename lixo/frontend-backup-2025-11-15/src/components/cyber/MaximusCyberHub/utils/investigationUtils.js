export const INVESTIGATION_TYPES = [
  { id: 'auto', name: 'Aurora Automático', description: 'IA decide a melhor estratégia', color: 'purple' },
  { id: 'defensive', name: 'Análise Defensiva', description: 'Foco em threat intel e detecção', color: 'blue' },
  { id: 'offensive', name: 'Red Team', description: 'Vulnerabilidades e vetores de ataque', color: 'red' },
  { id: 'full', name: 'Investigação Completa', description: 'Todos os serviços disponíveis', color: 'cyan' }
];

export const getTypeColor = (type) => {
  const colors = {
    auto: 'purple',
    defensive: 'blue',
    offensive: 'red',
    full: 'cyan'
  };
  return colors[type] || 'gray';
};

export const getStatusColor = (status) => {
  const colors = {
    running: 'yellow',
    completed: 'green',
    failed: 'red',
    warning: 'yellow'
  };
  return colors[status] || 'gray';
};
