import React from 'react';

const DarkWebModule = () => {
  return (
    <div className="space-y-6">
      <div className="border border-purple-400/50 rounded-lg bg-purple-400/5 p-6">
        <h2 className="text-purple-400 font-bold text-2xl mb-4 tracking-wider">
          🌑 DARK WEB MONITOR
        </h2>
        <p className="text-purple-400/70 text-sm mb-6">
          Monitoramento de atividades na dark web e mercados ocultos
        </p>

        <div className="bg-red-400/20 border border-red-400/50 rounded-lg p-6 text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <h3 className="text-red-400 font-bold text-xl mb-2">MÓDULO RESTRITO</h3>
          <p className="text-red-400/80 mb-4">
            Acesso ao Dark Web Monitor requer autorização especial
          </p>
          <p className="text-red-400/60 text-sm">
            Entre em contato com o administrador do sistema para solicitar acesso
          </p>

          <button
            className="mt-4 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 tracking-wider"
            onClick={() => alert('Funcionalidade em desenvolvimento - Requer autorização especial')}
          >
            🔐 SOLICITAR ACESSO
          </button>
        </div>

        <div className="bg-purple-400/10 border border-purple-400/30 rounded-lg p-4 mt-6">
          <h4 className="text-purple-400 font-bold mb-2">RECURSOS DISPONÍVEIS (COM AUTORIZAÇÃO)</h4>
          <ul className="text-purple-400/70 text-sm space-y-1">
            <li>• Monitoramento de mercados de dados vazados</li>
            <li>• Análise de fóruns de hackers</li>
            <li>• Detecção de credenciais comprometidas</li>
            <li>• Rastreamento de atividades criminosas</li>
            <li>• Alertas de ameaças emergentes</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default DarkWebModule;