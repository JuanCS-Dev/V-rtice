import React, { useState } from 'react';

const PhoneModule = () => {
  const [phone, setPhone] = useState('');
  const [analyzing, setAnalyzing] = useState(false);

  const handleAnalyze = async () => {
    if (!phone.trim()) {
      alert('Digite um número de telefone para analisar');
      return;
    }

    setAnalyzing(true);
    await new Promise(resolve => setTimeout(resolve, 1500));
    setAnalyzing(false);
  };

  return (
    <div className="space-y-6">
      <div className="border border-purple-400/50 rounded-lg bg-purple-400/5 p-6">
        <h2 className="text-purple-400 font-bold text-2xl mb-4 tracking-wider">
          📱 PHONE INTELLIGENCE
        </h2>
        <p className="text-purple-400/70 text-sm mb-6">
          Análise de números telefônicos, operadoras e aplicativos de mensagem
        </p>

        <div className="space-y-4">
          <input
            className="w-full bg-black/70 border border-purple-400/50 text-purple-400 placeholder-purple-400/50 p-3 rounded-lg focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400/20 font-mono"
            placeholder="+5562999999999"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          <button
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 tracking-wider disabled:opacity-50"
            onClick={handleAnalyze}
            disabled={analyzing}
          >
            {analyzing ? '📱 RASTREANDO...' : '🔍 RASTREAR TELEFONE'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default PhoneModule;