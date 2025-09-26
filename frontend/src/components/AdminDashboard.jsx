import React, { useState, useEffect } from 'react';

// --- Funções de Parsing de Métricas ---
// VERSÃO 2.0: Robusta e precisa
const parseMetrics = (text) => {
  let totalRequests = 0;
  let errorRequests = 0;
  let totalLatencySum = 0;
  let totalLatencyCount = 0;

  const lines = text.split('\n');

  // Expressão regular para capturar o status_code e o valor da métrica de total de pedidos
  const requestRegex = /api_requests_total{.*status_code="(\d{3})".*} (\d+\.?\d*)/;

  lines.forEach(line => {
    if (line.startsWith('#') || line.trim() === '') return;

    const requestMatch = line.match(requestRegex);
    if (requestMatch) {
      const statusCode = parseInt(requestMatch[1], 10);
      const value = parseFloat(requestMatch[2]);

      totalRequests += value;
      // Um erro é qualquer status code que não seja da família 2xx (sucesso)
      if (statusCode < 200 || statusCode >= 300) {
        errorRequests += value;
      }
    } else if (line.startsWith('api_response_time_seconds_sum')) {
      totalLatencySum += parseFloat(line.split(' ')[1]);
    } else if (line.startsWith('api_response_time_seconds_count')) {
      totalLatencyCount += parseFloat(line.split(' ')[1]);
    }
  });
  
  const averageLatency = totalLatencyCount > 0 ? (totalLatencySum / totalLatencyCount) * 1000 : 0;
  const errorRate = totalRequests > 0 ? (errorRequests / totalRequests) * 100 : 0;

  return {
    totalRequests,
    averageLatency: Math.round(averageLatency),
    errorRate: errorRate.toFixed(2)
  };
};
// ------------------------------------

const AdminDashboard = ({ setCurrentView }) => {
  const [metrics, setMetrics] = useState({ totalRequests: 0, averageLatency: 0, errorRate: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch('http://localhost:8000/metrics');
        if (!response.ok) { throw new Error(`Erro de rede: ${response.statusText}`); }
        const text = await response.text();
        const parsedData = parseMetrics(text);
        setMetrics(parsedData);
      } catch (error) {
        console.error("Falha ao buscar métricas:", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-screen w-screen bg-gray-900 text-gray-200 font-mono flex flex-col">
      <header className="flex items-center justify-between p-4 border-b border-gray-700 bg-gray-800">
        <h1 className="text-2xl font-bold tracking-wider">VÉRTICE - PAINEL ADMINISTRATIVO</h1>
        <button 
          onClick={() => setCurrentView('operator')}
          className="bg-green-600 hover:bg-green-700 text-black font-bold px-6 py-2 rounded transition-colors"
        >
          VOLTAR À VISTA DO OPERADOR
        </button>
      </header>

      <main className="flex-1 p-8">
        <h2 className="text-xl text-gray-400 mb-6">Métricas do Sistema em Tempo Real</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <h3 className="text-gray-400 text-sm font-bold uppercase">Consultas de Veículos (Total)</h3>
            <p className="text-4xl font-bold text-green-400 mt-2">
              {loading ? '...' : Math.round(metrics.totalRequests)}
            </p>
          </div>
          
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <h3 className="text-gray-400 text-sm font-bold uppercase">Latência Média</h3>
            <p className="text-4xl font-bold text-yellow-400 mt-2">
              {loading ? '...' : `${metrics.averageLatency}ms`}
            </p>
          </div>
          
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <h3 className="text-gray-400 text-sm font-bold uppercase">Taxa de Erros</h3>
            <p className="text-4xl font-bold text-red-400 mt-2">
              {loading ? '...' : `${metrics.errorRate}%`}
            </p>
          </div>

        </div>
      </main>
    </div>
  );
};

export default AdminDashboard;
