/**
 * Retorna variante de Badge baseada na severidade
 */
export const getSeverityVariant = (severity) => {
  const variants = {
    critical: "critical",
    high: "high",
    medium: "medium",
    low: "success",
  };
  return variants[severity?.toLowerCase()] || "cyber";
};
