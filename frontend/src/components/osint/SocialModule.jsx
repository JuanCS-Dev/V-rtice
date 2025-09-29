import React, { useState } from 'react';

const SocialModule = () => {
  const [platform, setPlatform] = useState('twitter');
  const [identifier, setIdentifier] = useState('');
  const [scraping, setScraping] = useState(false);

  const handleScrape = async () => {
    if (!identifier.trim()) {
      alert('Digite um identificador para extrair');
      return;
    }

    setScraping(true);
    await new Promise(resolve => setTimeout(resolve, 2000));
    setScraping(false);
  };

  return (
    <div className="space-y-6">
      <div className="border border-purple-400/50 rounded-lg bg-purple-400/5 p-6">
        <h2 className="text-purple-400 font-bold text-2xl mb-4 tracking-wider">
          🌐 SOCIAL MEDIA SCRAPER
        </h2>
        <p className="text-purple-400/70 text-sm mb-6">
          Coleta de dados em redes sociais com análise comportamental
        </p>

        <div className="space-y-4">
          <select
            className="w-full bg-black/70 border border-purple-400/50 text-purple-400 p-3 rounded-lg focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400/20"
            value={platform}
            onChange={(e) => setPlatform(e.target.value)}
          >
            <option value="twitter">Twitter/X</option>
            <option value="instagram">Instagram</option>
            <option value="linkedin">LinkedIn</option>
            <option value="facebook">Facebook</option>
            <option value="discord">Discord</option>
            <option value="telegram">Telegram</option>
          </select>

          <input
            className="w-full bg-black/70 border border-purple-400/50 text-purple-400 placeholder-purple-400/50 p-3 rounded-lg focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400/20 font-mono"
            placeholder="Username ou ID do perfil"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
          />

          <button
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 tracking-wider disabled:opacity-50"
            onClick={handleScrape}
            disabled={scraping}
          >
            {scraping ? '🌐 COLETANDO...' : '🚀 INICIAR SCRAPING'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SocialModule;