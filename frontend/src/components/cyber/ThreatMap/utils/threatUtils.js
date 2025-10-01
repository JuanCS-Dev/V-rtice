/**
 * Utility functions for threat visualization
 */

export const getThreatColor = (severity) => {
  const colors = {
    'critical': '#ff0040',
    'high': '#ff4000',
    'medium': '#ffaa00',
    'low': '#00aa00',
    'info': '#00aaff'
  };
  return colors[severity] || '#00aaff';
};

export const getThreatIcon = (type) => {
  const icons = {
    'malware': '🦠',
    'botnet': '🤖',
    'phishing': '🎣',
    'ddos': '💥',
    'exploit': '⚡',
    'scan': '🔍',
    'intrusion': '🔓',
    'data_breach': '📊',
    'ransomware': '🔒'
  };
  return icons[type] || '⚠️';
};

export const getThreatLabel = (type) => {
  const labels = {
    'malware': 'Malware',
    'botnet': 'Botnet',
    'phishing': 'Phishing',
    'ddos': 'DDoS',
    'exploit': 'Exploit',
    'scan': 'Port Scan',
    'intrusion': 'Intrusion',
    'data_breach': 'Data Breach',
    'ransomware': 'Ransomware'
  };
  return labels[type] || 'Unknown';
};
