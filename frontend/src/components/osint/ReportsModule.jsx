import React from 'react';

const ReportsModule = ({ results }) => {
  const exportPDF = () => {
    alert('Exportando relatório em PDF...');
  };

  const exportJSON = () => {
    if (results) {
      const dataStr = JSON.stringify(results, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `osint-report-${Date.now()}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } else {
      alert('Nenhum dado de investigação disponível para exportar');
    }
  };

  const generateGraphs = () => {
    alert('Gerando gráficos analíticos...');
  };

  return (
    <div className="space-y-6">
      <div className="border border-purple-400/50 rounded-lg bg-purple-400/5 p-6">
        <h2 className="text-purple-400 font-bold text-2xl mb-4 tracking-wider">
          📊 RELATÓRIOS OSINT
        </h2>
        <p className="text-purple-400/70 text-sm mb-6">
          Geração de relatórios completos de investigação e análise de dados
        </p>

        {results ? (
          <div className="space-y-4">
            <div className="bg-green-400/10 border border-green-400/30 rounded-lg p-4">
              <h3 className="text-green-400 font-bold mb-2">✅ DADOS DE INVESTIGAÇÃO DISPONÍVEIS</h3>
              <p className="text-green-400/80 text-sm mb-4">
                Relatório ID: {results.investigation_id}
              </p>

              <div className="grid grid-cols-3 gap-4">
                <button
                  className="bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white font-bold py-3 px-4 rounded-lg transition-all duration-300 text-sm"
                  onClick={exportPDF}
                >
                  📄 EXPORTAR PDF
                </button>
                <button
                  className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 text-white font-bold py-3 px-4 rounded-lg transition-all duration-300 text-sm"
                  onClick={exportJSON}
                >
                  💾 EXPORTAR JSON
                </button>
                <button
                  className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-500 hover:to-green-600 text-white font-bold py-3 px-4 rounded-lg transition-all duration-300 text-sm"
                  onClick={generateGraphs}
                >
                  📈 GERAR GRÁFICOS
                </button>
              </div>
            </div>

            {/* Preview dos dados */}
            <div className="bg-black/50 border border-purple-400/30 rounded-lg p-4">
              <h4 className="text-purple-400 font-bold mb-3">PREVIEW DO RELATÓRIO</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <strong className="text-purple-400">Nível de Risco:</strong>
                  <span className="ml-2 text-white/80">{results.risk_assessment?.risk_level || 'N/A'}</span>
                </div>
                <div>
                  <strong className="text-purple-400">Score de Risco:</strong>
                  <span className="ml-2 text-white/80">{results.risk_assessment?.risk_score || 'N/A'}</span>
                </div>
                <div>
                  <strong className="text-purple-400">Padrões Encontrados:</strong>
                  <span className="ml-2 text-white/80">{results.patterns_found?.length || 0}</span>
                </div>
                <div>
                  <strong className="text-purple-400">Recomendações:</strong>
                  <span className="ml-2 text-white/80">{results.recommendations?.length || 0}</span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-yellow-400/10 border border-yellow-400/30 rounded-lg p-6 text-center">
            <div className="text-6xl mb-4">📋</div>
            <h3 className="text-yellow-400 font-bold text-xl mb-2">NENHUM DADO DISPONÍVEL</h3>
            <p className="text-yellow-400/80 mb-4">
              Execute uma investigação no módulo Aurora AI para gerar relatórios
            </p>
            <p className="text-yellow-400/60 text-sm">
              Os dados da investigação aparecerão aqui automaticamente
            </p>
          </div>
        )}

        {/* Tipos de Relatórios Disponíveis */}
        <div className="bg-purple-400/10 border border-purple-400/30 rounded-lg p-4 mt-6">
          <h4 className="text-purple-400 font-bold mb-3">TIPOS DE RELATÓRIOS DISPONÍVEIS</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="bg-black/30 p-3 rounded">
              <strong className="text-purple-400">📄 Relatório Executivo PDF</strong>
              <p className="text-purple-400/70 mt-1">Relatório completo formatado para apresentação</p>
            </div>
            <div className="bg-black/30 p-3 rounded">
              <strong className="text-purple-400">💾 Dados Estruturados JSON</strong>
              <p className="text-purple-400/70 mt-1">Dados brutos para análise técnica</p>
            </div>
            <div className="bg-black/30 p-3 rounded">
              <strong className="text-purple-400">📈 Análise Visual</strong>
              <p className="text-purple-400/70 mt-1">Gráficos e visualizações dos dados</p>
            </div>
            <div className="bg-black/30 p-3 rounded">
              <strong className="text-purple-400">🔄 Relatório Dinâmico</strong>
              <p className="text-purple-400/70 mt-1">Dashboard interativo com filtros</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportsModule;