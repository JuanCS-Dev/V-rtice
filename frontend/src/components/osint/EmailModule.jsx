import React, { useState } from 'react';

const EmailModule = () => {
  const [email, setEmail] = useState('');
  const [analyzing, setAnalyzing] = useState(false);

  const handleAnalyze = async () => {
    if (!email.trim()) {
      alert('Digite um email para analisar');
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
          📧 EMAIL ANALYZER
        </h2>
        <p className="text-purple-400/70 text-sm mb-6">
          Análise de segurança, vazamentos e reputação de endereços de email
        </p>

        <div className="space-y-4">
          <input
            className="w-full bg-black/70 border border-purple-400/50 text-purple-400 placeholder-purple-400/50 p-3 rounded-lg focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400/20 font-mono"
            placeholder="Digite o email..."
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 tracking-wider disabled:opacity-50"
            onClick={handleAnalyze}
            disabled={analyzing}
          >
            {analyzing ? '📧 ANALISANDO...' : '🔍 ANALISAR EMAIL'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default EmailModule;