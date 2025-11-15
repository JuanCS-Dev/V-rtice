/**
 * Retorna classes CSS baseadas no status do domínio
 */
export const getStatusColor = (status) => {
  const colors = {
    malicious: 'text-red-400 border-red-400',
    suspicious: 'text-orange-400 border-orange-400',
    clean: 'text-green-400 border-green-400'
  };
  return colors[status] || 'text-gray-400 border-gray-400';
};

/**
 * Retorna variante de Badge baseada no status
 */
export const getStatusVariant = (status) => {
  const variants = {
    malicious: 'critical',
    suspicious: 'warning',
    clean: 'success'
  };
  return variants[status] || 'default';
};

/**
 * Retorna cor para barra de progresso baseada no score
 */
export const getScoreColor = (score) => {
  if (score < 30) return 'bg-red-400';
  if (score < 70) return 'bg-orange-400';
  return 'bg-green-400';
};

/**
 * Retorna cor do texto baseada no score
 */
export const getScoreTextColor = (score) => {
  if (score < 30) return 'text-red-400';
  if (score < 70) return 'text-orange-400';
  return 'text-green-400';
};
