import React from 'react';

// Recebe a função setCurrentView como prop
const Footer = ({ searchHistory = [], setCurrentView }) => {
  return (
    <footer className="border-t border-green-400/30 bg-black/50 backdrop-blur-sm p-2">
      <div className="flex justify-between items-center text-xs">
        <div className="flex space-x-6 items-center">
          <span className="text-green-400">CONEXÃO: SEGURA</span>
          <span className="text-green-400">SERVIDOR: ONLINE</span>
          <span className="text-green-400">USUÁRIO: OPERADOR_001</span>
          {searchHistory.length > 0 && (
            <span className="text-green-400">CONSULTAS: {searchHistory.length}</span>
          )}
          {/* O BOTÃO SECRETO */}
          <button 
            onClick={() => setCurrentView('admin')}
            className="text-gray-500 hover:text-yellow-400 transition-colors border border-gray-600 px-2 py-1 rounded"
          >
            ADMIN
          </button>
        </div>
        <div className="text-green-400/70">
          PROJETO VÉRTICE v2.0 | SSP-GO | CLASSIFICAÇÃO: CONFIDENCIAL
        </div>
      </div>
    </footer>
  );
};

export default Footer;
