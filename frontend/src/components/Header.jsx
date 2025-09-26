import React from 'react';

const Header = ({ currentTime, placa, setPlaca, loading, handleSearch, handleKeyPress, searchHistory }) => {
  return (
    <header className="relative border-b border-green-400/30 bg-black/50 backdrop-blur-sm">
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 border-2 border-green-400 rounded-lg flex items-center justify-center bg-green-400/10">
            <span className="text-green-400 font-bold text-xl">V</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-green-400 tracking-wider">
              PROJETO VÉRTICE
            </h1>
            <p className="text-green-400/70 text-sm tracking-widest">SISTEMA DE INTELIGÊNCIA CRIMINAL</p>
          </div>
        </div>
        
        <div className="text-right">
          <div className="text-green-400 font-bold text-lg">
            {currentTime.toLocaleTimeString()}
          </div>
          <div className="text-green-400/70 text-sm">
            {currentTime.toLocaleDateString('pt-BR')}
          </div>
        </div>
      </div>

      <div className="p-4 bg-gradient-to-r from-green-900/20 to-blue-900/20">
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <input
              type="text"
              value={placa}
              onChange={(e) => setPlaca(e.target.value.toUpperCase())}
              onKeyPress={handleKeyPress}
              placeholder=">>> INSERIR PLACA DO VEÍCULO"
              className="w-full bg-black/70 border border-green-400/50 text-green-400 placeholder-green-400/50 p-3 rounded-lg focus:border-green-400 focus:outline-none focus:ring-2 focus:ring-green-400/20 font-mono text-lg tracking-widest"
              disabled={loading}
            />
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              {loading && (
                <div className="w-6 h-6 border-2 border-green-400 border-t-transparent rounded-full animate-spin"></div>
              )}
            </div>
          </div>
          
          <button
            onClick={handleSearch}
            disabled={loading || !placa.trim()}
            className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-500 hover:to-green-600 disabled:from-gray-600 disabled:to-gray-700 text-black font-bold px-8 py-3 rounded-lg transition-all duration-300 disabled:cursor-not-allowed tracking-widest"
          >
            {loading ? 'PROCESSANDO...' : 'EXECUTAR CONSULTA'}
          </button>
        </div>

        {searchHistory.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            <span className="text-green-400/50 text-xs">HISTÓRICO:</span>
            {searchHistory.slice(0, 5).map((historicPlaca, index) => (
              <button
                key={index}
                onClick={() => setPlaca(historicPlaca)}
                className="px-2 py-1 bg-green-400/10 text-green-400/70 text-xs rounded hover:bg-green-400/20 transition-all"
              >
                {historicPlaca}
              </button>
            ))}
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
