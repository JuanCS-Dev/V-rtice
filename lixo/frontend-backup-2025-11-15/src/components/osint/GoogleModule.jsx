import React, { useState } from "react";
import { scanWithGoogleDorks } from "@/api/worldClassTools";
import logger from "@/utils/logger";

const GoogleModule = () => {
  const [target, setTarget] = useState("");
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [selectedEngines, setSelectedEngines] = useState([]);
  const [maxResults, setMaxResults] = useState(10);
  const [scanning, setScanning] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const categories = [
    { id: "files", label: "Arquivos Sensíveis", icon: "📄" },
    { id: "credentials", label: "Credenciais", icon: "🔑" },
    { id: "directories", label: "Diretórios", icon: "📁" },
    { id: "vulnerabilities", label: "Vulnerabilidades", icon: "🔴" },
    { id: "configurations", label: "Configurações", icon: "⚙️" },
    { id: "databases", label: "Databases", icon: "💾" },
    { id: "backups", label: "Backups", icon: "💿" },
    { id: "social", label: "Social Media", icon: "📱" },
  ];

  const engines = [
    { id: "google", label: "Google", icon: "🔍" },
    { id: "bing", label: "Bing", icon: "🅱️" },
    { id: "duckduckgo", label: "DuckDuckGo", icon: "🦆" },
    { id: "yandex", label: "Yandex", icon: "🇷🇺" },
  ];

  const toggleCategory = (categoryId) => {
    setSelectedCategories((prev) =>
      prev.includes(categoryId)
        ? prev.filter((c) => c !== categoryId)
        : [...prev, categoryId],
    );
  };

  const toggleEngine = (engineId) => {
    setSelectedEngines((prev) =>
      prev.includes(engineId)
        ? prev.filter((e) => e !== engineId)
        : [...prev, engineId],
    );
  };

  const handleScan = async () => {
    if (!target.trim()) {
      alert("Digite um domínio para escanear");
      return;
    }

    setScanning(true);
    setError(null);
    setResults(null);

    try {
      const response = await scanWithGoogleDorks(target.trim(), {
        categories: selectedCategories.length > 0 ? selectedCategories : null,
        engines: selectedEngines.length > 0 ? selectedEngines : null,
        maxResultsPerDork: maxResults,
      });

      if (response.status === "success") {
        setResults(response.data);
      } else {
        setError("Erro ao executar scan Google Dorks");
      }
    } catch (err) {
      setError(`Erro: ${err.message}`);
      logger.error("Google Dork Scan Error:", err);
    } finally {
      setScanning(false);
    }
  };

  const getRiskColor = (score) => {
    if (score >= 75) return "text-red-400 border-red-400 bg-red-400/20";
    if (score >= 50)
      return "text-orange-400 border-orange-400 bg-orange-400/20";
    if (score >= 25)
      return "text-yellow-400 border-yellow-400 bg-yellow-400/20";
    return "text-green-400 border-green-400 bg-green-400/20";
  };

  const getCategoryIcon = (category) => {
    const cat = categories.find((c) => c.id === category);
    return cat ? cat.icon : "🔍";
  };

  return (
    <div className="space-y-6">
      <div className="border border-red-400/50 rounded-lg bg-red-400/5 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-red-400 font-bold text-2xl tracking-wider flex items-center">
              🌐 GOOGLE DORK SCANNER
              <span className="ml-3 text-xs bg-gradient-to-r from-red-600 to-pink-600 text-white px-2 py-1 rounded">
                ⭐ WORLD-CLASS
              </span>
            </h2>
            <p className="text-red-400/70 text-sm mt-1">
              Multi-Engine Dorking: Google, Bing, DuckDuckGo, Yandex | 1000+
              Templates
            </p>
          </div>
        </div>

        {/* Configuration Panel */}
        <div className="space-y-4 mb-6">
          {/* Target Input */}
          <div>
            <label
              htmlFor="target-domain-input"
              className="text-red-400/80 text-xs font-bold tracking-wider block mb-2"
            >
              🎯 TARGET DOMAIN
            </label>
            <input
              id="target-domain-input"
              className="w-full bg-black/70 border border-red-400/50 text-red-400 placeholder-red-400/50 p-3 rounded-lg focus:border-red-400 focus:outline-none focus:ring-2 focus:ring-red-400/20 font-mono text-lg"
              placeholder="example.com"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleScan()}
            />
          </div>

          {/* Categories Selection */}
          <div>
            <div className="text-red-400/80 text-xs font-bold tracking-wider mb-2">
              📋 DORK CATEGORIES (deixe vazio para todas)
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => toggleCategory(cat.id)}
                  className={`p-2 rounded border text-xs font-medium transition-all ${
                    selectedCategories.includes(cat.id)
                      ? "bg-red-400/20 border-red-400 text-red-400"
                      : "bg-black/30 border-red-400/30 text-red-400/60 hover:border-red-400/50"
                  }`}
                >
                  <span className="mr-1">{cat.icon}</span>
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          {/* Engines Selection */}
          <div>
            <div className="text-red-400/80 text-xs font-bold tracking-wider mb-2">
              🚀 SEARCH ENGINES (deixe vazio para todos)
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {engines.map((engine) => (
                <button
                  key={engine.id}
                  onClick={() => toggleEngine(engine.id)}
                  className={`p-2 rounded border text-xs font-medium transition-all ${
                    selectedEngines.includes(engine.id)
                      ? "bg-orange-400/20 border-orange-400 text-orange-400"
                      : "bg-black/30 border-red-400/30 text-red-400/60 hover:border-orange-400/50"
                  }`}
                >
                  <span className="mr-1">{engine.icon}</span>
                  {engine.label}
                </button>
              ))}
            </div>
          </div>

          {/* Max Results */}
          <div>
            <label className="text-red-400/80 text-xs font-bold tracking-wider block mb-2">
              📊 MAX RESULTS PER DORK: {maxResults}
            </label>
            <input
              type="range"
              min="5"
              max="50"
              step="5"
              value={maxResults}
              onChange={(e) => setMaxResults(Number(e.target.value))}
              className="w-full"
            />
          </div>

          {/* Scan Button */}
          <button
            className="w-full bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-500 hover:to-pink-500 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 tracking-wider disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={handleScan}
            disabled={scanning}
          >
            {scanning ? (
              <>
                <span className="animate-pulse">🔍 SCANNING...</span>
              </>
            ) : (
              "🚀 EXECUTE DORK SCAN"
            )}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 border border-red-400/50 rounded-lg bg-red-400/10">
            <p className="text-red-400">❌ {error}</p>
          </div>
        )}

        {/* Results Display */}
        {results && !scanning && (
          <div className="bg-black/50 border border-red-400/30 rounded-lg p-6">
            {/* Summary Stats */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-black/40 border border-red-400/30 rounded-lg p-3 text-center">
                <div className="text-red-400 text-2xl font-bold">
                  {results.total_urls || 0}
                </div>
                <div className="text-red-400/70 text-xs">URLs Found</div>
              </div>
              <div className="bg-black/40 border border-orange-400/30 rounded-lg p-3 text-center">
                <div className="text-orange-400 text-2xl font-bold">
                  {results.total_dorks_executed || 0}
                </div>
                <div className="text-orange-400/70 text-xs">Dorks Executed</div>
              </div>
              <div className="bg-black/40 border border-yellow-400/30 rounded-lg p-3 text-center">
                <div className="text-yellow-400 text-2xl font-bold">
                  {results.engines_used?.length || 0}
                </div>
                <div className="text-yellow-400/70 text-xs">Engines Used</div>
              </div>
              <div
                className={`rounded-lg p-3 text-center border ${getRiskColor(results.risk_score || 0)}`}
              >
                <div className="text-2xl font-bold">
                  {results.risk_score?.toFixed(1) || 0}
                </div>
                <div className="text-xs opacity-70">Risk Score</div>
              </div>
            </div>

            {/* Risk Assessment */}
            {results.risk_score > 0 && (
              <div
                className={`mb-6 p-4 rounded-lg border ${getRiskColor(results.risk_score)}`}
              >
                <h4 className="font-bold mb-2">⚠️ RISK ASSESSMENT</h4>
                <p className="text-sm opacity-90">
                  {results.risk_score >= 75 &&
                    "CRITICAL: Exposição severa detectada! Ação imediata necessária."}
                  {results.risk_score >= 50 &&
                    results.risk_score < 75 &&
                    "HIGH: Várias exposições encontradas. Revisar urgentemente."}
                  {results.risk_score >= 25 &&
                    results.risk_score < 50 &&
                    "MEDIUM: Algumas exposições detectadas. Investigar."}
                  {results.risk_score < 25 &&
                    "LOW: Exposição mínima. Monitorar periodicamente."}
                </p>
              </div>
            )}

            {/* Results by Category */}
            {results.results_by_category &&
            Object.keys(results.results_by_category).length > 0 ? (
              <div className="space-y-4">
                <h3 className="text-red-400 font-bold text-lg mb-3">
                  📊 RESULTS BY CATEGORY
                </h3>
                {Object.entries(results.results_by_category).map(
                  ([category, categoryResults]) => (
                    <div
                      key={category}
                      className="bg-red-400/10 border border-red-400/30 rounded-lg p-4"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-red-400 font-medium capitalize flex items-center">
                          <span className="mr-2">
                            {getCategoryIcon(category)}
                          </span>
                          {category.replace(/_/g, " ")}
                        </h4>
                        <span className="text-red-400/60 text-sm">
                          {categoryResults.length} resultado(s)
                        </span>
                      </div>

                      <div className="space-y-2 max-h-60 overflow-y-auto">
                        {categoryResults.slice(0, 20).map((result, idx) => (
                          <div
                            key={idx}
                            className="bg-black/40 border border-red-400/20 rounded p-3 hover:border-red-400/40 transition-all"
                          >
                            <div className="flex justify-between items-start mb-2">
                              <a
                                href={result.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-red-300 hover:text-red-200 text-sm break-all flex-1"
                              >
                                {result.url}
                              </a>
                            </div>
                            <div className="flex justify-between items-center text-xs">
                              <span className="text-red-400/50 font-mono">
                                Engine: {result.engine}
                              </span>
                              <span className="text-red-400/50">
                                Dork: {result.dork_category}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ),
                )}
              </div>
            ) : (
              <div className="text-center p-8 text-red-400/60">
                <div className="text-4xl mb-2">✅</div>
                <p>Nenhuma exposição crítica encontrada.</p>
                <p className="text-xs mt-2">
                  O domínio parece estar seguro contra Google Dorking básico.
                </p>
              </div>
            )}

            {/* Execution Time */}
            {results.execution_time && (
              <div className="mt-6 text-center text-red-400/60 text-xs">
                ⏱️ Execution Time: {results.execution_time}s
              </div>
            )}
          </div>
        )}

        {/* Info Box */}
        <div className="mt-6 bg-red-400/10 border border-red-400/30 rounded-lg p-4">
          <h4 className="text-red-400 font-bold mb-3">
            🧰 SUPERIOR CAPABILITIES
          </h4>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-black/30 p-2 rounded">
              <span className="text-red-400 font-bold">✅ Multi-Engine</span>
              <p className="text-red-300">Google, Bing, DuckDuckGo, Yandex</p>
            </div>
            <div className="bg-black/30 p-2 rounded">
              <span className="text-red-400 font-bold">✅ 1000+ Templates</span>
              <p className="text-red-300">8 categories, auto-generated dorks</p>
            </div>
            <div className="bg-black/30 p-2 rounded">
              <span className="text-red-400 font-bold">✅ Risk Scoring</span>
              <p className="text-red-300">Intelligent 0-100 risk assessment</p>
            </div>
            <div className="bg-black/30 p-2 rounded">
              <span className="text-red-400 font-bold">
                ✅ CAPTCHA Detection
              </span>
              <p className="text-red-300">Graceful anti-bot handling</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GoogleModule;
