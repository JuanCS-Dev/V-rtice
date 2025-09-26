import React from 'react';

// 1. RECEBER PROP: Adicionar onGerarRelatorio
const DossierPanel = ({ loading, error, dossierData, onVerOcorrencias, onMarcarSuspeito, placasSuspeitas, onGerarRelatorio }) => {
  if (error) {
    return (
      <div className="w-96 border-r border-green-400/30 bg-black/20 backdrop-blur-sm overflow-y-auto p-6 text-center flex-shrink-0">
        <div className="text-red-400 font-bold text-lg mb-2">⚠️ ERRO DE SISTEMA</div>
        <p className="text-red-400/70">{error}</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="w-96 border-r border-green-400/30 bg-black/20 backdrop-blur-sm overflow-y-auto p-6 text-center flex-shrink-0">
        <div className="inline-block w-16 h-16 border-4 border-green-400 border-t-transparent rounded-full animate-spin mb-4"></div>
        <div className="text-green-400 font-bold text-lg">PROCESSANDO DADOS...</div>
        <div className="text-green-400/70 mt-2">Consultando bases de dados...</div>
      </div>
    );
  }

  if (!dossierData) {
    return (
      <div className="w-96 border-r border-green-400/30 bg-black/20 backdrop-blur-sm overflow-y-auto p-6 text-center text-green-400/50 flex-shrink-0">
        <div className="text-6xl mb-4">🔍</div>
        <p>AGUARDANDO CONSULTA...</p>
        <p className="text-xs mt-2">Digite uma placa para iniciar a análise</p>
      </div>
    );
  }
  
  const isSuspeito = placasSuspeitas.has(dossierData.placa);

  return (
    <div className="w-96 border-r border-green-400/30 bg-black/20 backdrop-blur-sm overflow-y-auto p-4 flex flex-col flex-shrink-0">
      <div className="border border-green-400/50 rounded-lg bg-green-400/5 p-4 mb-4 flex-grow">
        <h3 className="text-green-400 font-bold text-xl mb-4 tracking-wider">DOSSIÊ VEICULAR</h3>
        <div className="mb-4 flex items-center space-x-2">
          <div className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${
            dossierData.riskLevel === 'HIGH' ? 'bg-red-500/20 text-red-400 border border-red-400/50' :
            dossierData.riskLevel === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-400/50' :
            'bg-green-500/20 text-green-400 border border-green-400/50'
          }`}>
            RISCO: {dossierData.riskLevel || 'BAIXO'}
          </div>
          {isSuspeito && (
            <div className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-orange-500/20 text-orange-400 border border-orange-400/50">
              MARCADO
            </div>
          )}
        </div>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div><span className="text-green-400/70 text-xs block">PLACA</span><span className="text-green-400 font-bold text-lg">{dossierData.placa}</span></div>
            <div><span className="text-green-400/70 text-xs block">SITUAÇÃO</span><span className="text-green-400 font-bold">{dossierData.situacao}</span></div>
          </div>
          <div><span className="text-green-400/70 text-xs block">VEÍCULO</span><span className="text-green-400 font-bold">{dossierData.marca} {dossierData.modelo}</span></div>
          <div className="grid grid-cols-2 gap-4">
            <div><span className="text-green-400/70 text-xs block">ANO</span><span className="text-green-400">{dossierData.ano}</span></div>
            <div><span className="text-green-400/70 text-xs block">COR</span><span className="text-green-400">{dossierData.cor}</span></div>
          </div>
          <div><span className="text-green-400/70 text-xs block">CHASSI</span><span className="text-green-400 font-mono">{dossierData.chassi}</span></div>
          <div><span className="text-green-400/70 text-xs block">LOCALIZAÇÃO</span><span className="text-green-400">{dossierData.municipio} - {dossierData.uf}</span></div>
        </div>
      </div>
      <div className="space-y-2 flex-shrink-0">
        {/* 2. CONECTAR BOTÃO: Adicionar o onClick aqui */}
        <button 
          onClick={onGerarRelatorio}
          className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white font-bold py-2 px-4 rounded hover:from-blue-500 hover:to-blue-600 transition-all">
          📊 GERAR RELATÓRIO COMPLETO
        </button>
        <button 
          onClick={onVerOcorrencias}
          className="w-full bg-gradient-to-r from-purple-600 to-purple-700 text-white font-bold py-2 px-4 rounded hover:from-purple-500 hover:to-purple-600 transition-all"
        >
          🔍 HISTÓRICO DE OCORRÊNCIAS
        </button>
        <button 
          onClick={() => onMarcarSuspeito(dossierData.placa)}
          disabled={isSuspeito}
          className={`w-full font-bold py-2 px-4 rounded transition-all ${
            isSuspeito
              ? 'bg-red-800 text-red-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-orange-600 to-orange-700 text-white hover:from-orange-500 hover:to-orange-600'
          }`}
        >
          {isSuspeito ? '✓ MARCADO COMO SUSPEITO' : '🚨 MARCAR COMO SUSPEITO'}
        </button>
      </div>
    </div>
  );
};
export default DossierPanel;
