/**
 * Retorna classes CSS baseadas no nível de ameaça
 */
export const getThreatColor = (level) => {
  const colors = {
    critical: "text-red-400 border-red-400 bg-red-400/20",
    high: "text-orange-400 border-orange-400 bg-orange-400/20",
    medium: "text-yellow-400 border-yellow-400 bg-yellow-400/20",
    low: "text-green-400 border-green-400 bg-green-400/20",
  };
  return colors[level] || "text-gray-400 border-gray-400 bg-gray-400/20";
};

/**
 * Retorna cor para barra de progresso baseada no score
 */
export const getScoreColor = (score) => {
  if (score < 30) return "bg-red-400";
  if (score < 70) return "bg-orange-400";
  return "bg-green-400";
};

/**
 * Retorna variante de Badge baseada no nível de ameaça
 */
export const getThreatBadgeVariant = (level) => {
  const variants = {
    critical: "critical",
    high: "high",
    medium: "medium",
    low: "success",
  };
  return variants[level] || "default";
};

/**
 * Retorna variante de categoria de ameaça
 */
export const getThreatCategoryVariant = (category) => {
  const critical = ["malware", "botnet", "ransomware"];
  const high = ["exploit", "backdoor", "trojan"];

  if (critical.includes(category.toLowerCase())) return "critical";
  if (high.includes(category.toLowerCase())) return "high";
  return "warning";
};
