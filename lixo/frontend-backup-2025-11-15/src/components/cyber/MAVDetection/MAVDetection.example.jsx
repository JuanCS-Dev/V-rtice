/**
 * MAV Detection - Exemplo de Uso
 *
 * Este arquivo demonstra como integrar o widget MAVDetection
 * em diferentes contextos da aplicação Vértice.
 */

import React from "react";
import { MAVDetection } from "./MAVDetection";

/**
 * Exemplo 1: Uso Básico
 * Widget standalone em uma página dedicada
 */
export const BasicExample = () => {
  return (
    <div style={{ padding: "20px" }}>
      <h1>Detecção de Campanhas MAV</h1>
      <MAVDetection />
    </div>
  );
};

/**
 * Exemplo 2: Integração no Offensive Dashboard
 * Widget como parte do dashboard de segurança ofensiva
 */
export const DashboardIntegration = () => {
  return (
    <div className="offensive-dashboard">
      <div className="dashboard-header">
        <h1>🛡️ Offensive Security Arsenal</h1>
        <p>Ferramentas de Ataque e Defesa</p>
      </div>

      <div className="dashboard-grid">
        {/* Outros widgets */}
        <div className="widget-network-recon">
          {/* NetworkRecon component */}
        </div>

        <div className="widget-vuln-intel">{/* VulnIntel component */}</div>

        {/* MAV Detection Widget */}
        <div className="widget-mav-detection">
          <MAVDetection />
        </div>
      </div>
    </div>
  );
};

/**
 * Exemplo 3: Integração no Cockpit Soberano
 * Widget com contexto de inteligência nacional
 */
export const CockpitIntegration = () => {
  return (
    <div className="cockpit-soberano">
      <div className="intelligence-panel">
        <h2>🇧🇷 Inteligência Nacional</h2>

        {/* Social Defense Section */}
        <div className="social-defense">
          <h3>Defesa de Redes Sociais</h3>
          <MAVDetection />
        </div>

        {/* Outras seções */}
        <div className="threat-monitoring">
          {/* Threat monitoring components */}
        </div>
      </div>
    </div>
  );
};

/**
 * Exemplo 4: Uso com Estado Externo
 * Controlando o componente através de props (futuro)
 */
export const ControlledExample = () => {
  const [detectionResults, setDetectionResults] = React.useState(null);

  const handleDetectionComplete = (results) => {
    setDetectionResults(results);
    // Processar resultados externamente
    // Ex: enviar para analytics, alertar usuário, etc.
    console.log("MAV Campaign detected:", results);
  };

  return (
    <div>
      <MAVDetection
      // Futuras props opcionais
      // onDetectionComplete={handleDetectionComplete}
      // autoRefresh={true}
      // theme="dark"
      />

      {detectionResults && (
        <div className="external-summary">
          <h3>Resumo Executivo</h3>
          <p>Severidade: {detectionResults.severity}</p>
          <p>Confiança: {detectionResults.confidence_score}%</p>
        </div>
      )}
    </div>
  );
};

/**
 * Exemplo 5: Integração com Roteamento
 * Widget em uma rota dedicada
 */
export const RouteExample = () => {
  // Em seu router (React Router, Next.js, etc.)
  /*
  <Route path="/security/mav-detection" element={<MAVDetectionPage />} />
  */

  return (
    <div className="page-container">
      <nav className="breadcrumb">
        <a href="/">Home</a> /<a href="/security">Security</a> /
        <span>MAV Detection</span>
      </nav>

      <div className="page-content">
        <MAVDetection />
      </div>

      <aside className="page-sidebar">
        <h3>Recursos Relacionados</h3>
        <ul>
          <li>
            <a href="/security/behavioral-analyzer">Behavioral Analyzer</a>
          </li>
          <li>
            <a href="/security/traffic-analyzer">Traffic Analyzer</a>
          </li>
        </ul>
      </aside>
    </div>
  );
};

/**
 * Exemplo 6: Dados de Teste Programáticos
 * Útil para testes automatizados
 */
export const TestingExample = () => {
  const mockPosts = [
    {
      id: "1",
      text: "Narrativa coordenada sobre eleições #FakeNews",
      author: "bot_account_1",
      timestamp: new Date(Date.now() - 120000).toISOString(),
      engagement: { likes: 500, shares: 200 },
    },
    {
      id: "2",
      text: "Narrativa coordenada sobre eleições #FakeNews",
      author: "bot_account_2",
      timestamp: new Date(Date.now() - 115000).toISOString(),
      engagement: { likes: 480, shares: 195 },
    },
    {
      id: "3",
      text: "Narrativa coordenada sobre eleições #FakeNews",
      author: "bot_account_3",
      timestamp: new Date(Date.now() - 110000).toISOString(),
      engagement: { likes: 510, shares: 205 },
    },
  ];

  const mockAccounts = [
    {
      id: "bot_account_1",
      created_at: new Date(Date.now() - 86400000 * 15).toISOString(),
      followers_count: 50,
      following_count: 5000,
      posts_count: 1000,
    },
    {
      id: "bot_account_2",
      created_at: new Date(Date.now() - 86400000 * 14).toISOString(),
      followers_count: 48,
      following_count: 5100,
      posts_count: 1050,
    },
    {
      id: "bot_account_3",
      created_at: new Date(Date.now() - 86400000 * 16).toISOString(),
      followers_count: 52,
      following_count: 4900,
      posts_count: 980,
    },
  ];

  return (
    <div className="testing-environment">
      <h2>🧪 Ambiente de Testes</h2>
      <pre>Posts: {JSON.stringify(mockPosts, null, 2)}</pre>
      <pre>Accounts: {JSON.stringify(mockAccounts, null, 2)}</pre>

      <MAVDetection />
    </div>
  );
};

/**
 * Exemplo 7: Monitoramento em Tempo Real (Conceitual)
 * Futuro: WebSocket integration para streaming de alertas
 */
export const RealTimeExample = () => {
  const [alerts, setAlerts] = React.useState([]);

  React.useEffect(() => {
    // Futuro: WebSocket connection
    /*
    const ws = new WebSocket('wss://api.vertice.com.br/mav/stream');

    ws.onmessage = (event) => {
      const alert = JSON.parse(event.data);
      setAlerts(prev => [alert, ...prev].slice(0, 10));
    };

    return () => ws.close();
    */
  }, []);

  return (
    <div className="real-time-monitor">
      <div className="alerts-stream">
        <h3>🔴 Alertas em Tempo Real</h3>
        {alerts.map((alert, idx) => (
          <div key={idx} className="alert-item">
            {alert.message}
          </div>
        ))}
      </div>

      <div className="detection-widget">
        <MAVDetection />
      </div>
    </div>
  );
};

/**
 * Exemplo 8: Integração com API de Relatórios
 * Exportar resultados para análise posterior
 */
export const ReportingExample = () => {
  const exportToPDF = async (results) => {
    // Futuro: Gerar PDF com resultados da análise
    const reportData = {
      timestamp: new Date().toISOString(),
      campaign_type: results.campaign_type,
      severity: results.severity,
      details: results,
    };

    // API call para gerar relatório
    /*
    await fetch('/api/reports/mav/export', {
      method: 'POST',
      body: JSON.stringify(reportData),
      headers: { 'Content-Type': 'application/json' },
    });
    */

    console.log("Report data:", reportData);
  };

  return (
    <div>
      <MAVDetection />

      <div className="export-options">
        <button onClick={() => exportToPDF()}>📄 Exportar para PDF</button>
        <button>📊 Exportar para Excel</button>
        <button>📧 Enviar por Email</button>
      </div>
    </div>
  );
};

// Export all examples
export default {
  BasicExample,
  DashboardIntegration,
  CockpitIntegration,
  ControlledExample,
  RouteExample,
  TestingExample,
  RealTimeExample,
  ReportingExample,
};
