import React from 'react';

const Footer = ({ searchHistory = [] }) => {
  return (
    <footer className="border-t border-green-400/30 bg-black/50 backdrop-blur-sm p-3">
      <div className="flex justify-between items-center text-xs">
        <div className="flex space-x-6 items-center">
          <span className="text-green-400 flex items-center">
            <span className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></span>
            CONEXÃO: SEGURA
          </span>
          <span className="text-green-400 flex items-center">
            <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
            SERVIDOR: ONLINE
          </span>
          <span className="text-green-400">USUÁRIO: OPERADOR_001</span>
          {searchHistory.length > 0 && (
            <span className="text-green-400">CONSULTAS REALIZADAS: {searchHistory.length}</span>
          )}
        </div>
        <div className="text-green-400/70 font-mono">
          PROJETO VÉRTICE v2.4.0 | SSP-GO | CLASSIFICAÇÃO: CONFIDENCIAL
        </div>
      </div>
    </footer>
  );
};

export default Footer;
