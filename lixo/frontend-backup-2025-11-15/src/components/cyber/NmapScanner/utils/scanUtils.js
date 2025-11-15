/**
 * Perfis de scan predefinidos
 */
export const SCAN_PROFILES = {
  quick: "-T4 -F",
  intense: "-T4 -A -v",
  stealth: "-sS -T4",
  ping: "-sn",
  comprehensive: "-T4 -A -v --script=default,vuln",
};

/**
 * Retorna cor de risco baseada no serviço
 */
export const getServiceRiskColor = (service) => {
  const highRisk = ["telnet", "ftp", "rsh", "rlogin", "snmp", "tftp"];
  const mediumRisk = ["ssh", "http", "https", "mysql", "postgresql", "rdp"];

  if (highRisk.includes(service)) return "text-red-400";
  if (mediumRisk.includes(service)) return "text-orange-400";
  return "text-green-400";
};

/**
 * Retorna ícone de risco baseado no serviço
 */
export const getRiskIcon = (service) => {
  const highRisk = ["telnet", "ftp", "rsh", "rlogin", "snmp", "tftp"];
  const mediumRisk = ["ssh", "http", "https", "mysql", "postgresql", "rdp"];

  if (highRisk.includes(service)) return "🔴";
  if (mediumRisk.includes(service)) return "🟡";
  return "🟢";
};

/**
 * Retorna variante de Badge baseada no risco do serviço
 */
export const getServiceRiskVariant = (service) => {
  const highRisk = ["telnet", "ftp", "rsh", "rlogin", "snmp", "tftp"];
  const mediumRisk = ["ssh", "http", "https", "mysql", "postgresql", "rdp"];

  if (highRisk.includes(service)) return "critical";
  if (mediumRisk.includes(service)) return "warning";
  return "success";
};

/**
 * Retorna variante de Badge baseada no estado da porta
 */
export const getPortStateVariant = (state) => {
  const variants = {
    open: "success",
    closed: "default",
    filtered: "warning",
  };
  return variants[state] || "default";
};
