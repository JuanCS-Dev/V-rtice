/**
 * Retorna variante de Badge baseada na severidade
 */
export const getSeverityVariant = (severity) => {
  const variants = {
    critical: "critical",
    high: "high",
    medium: "medium",
    info: "cyber",
  };
  return variants[severity] || "default";
};

/**
 * Retorna ícone baseado na severidade
 */
export const getSeverityIcon = (severity) => {
  const icons = {
    critical: "🚨",
    high: "⚠️",
    medium: "🔍",
    info: "ℹ️",
  };
  return icons[severity] || "📋";
};
