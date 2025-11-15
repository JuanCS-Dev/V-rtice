import React from "react";
import { ThemeSelector } from "./shared/ThemeSelector/ThemeSelector";
import { formatTime, formatDate } from "../utils/dateHelpers";

const Header = ({
  currentTime,
  placa,
  setPlaca,
  loading,
  handleSearch,
  handleKeyPress,
  searchHistory,
  setCurrentView,
  currentView,
}) => {
  const navigationModules = [
    {
      id: "main",
      label: "OPERAÇÕES GERAIS",
      icon: "🏠",
      description: "Consultas Veiculares e Mapa Tático",
      color: "green",
    },
    {
      id: "cyber",
      label: "CYBER SECURITY",
      icon: "🛡️",
      description: "Análise de Redes e Ameaças Digitais",
      color: "cyan",
    },
    {
      id: "osint",
      label: "INTELIGÊNCIA SOCIAL",
      icon: "🕵️",
      description: "Investigação em Mídias Sociais",
      color: "purple",
    },
    {
      id: "terminal",
      label: "TERMINAL CLI",
      icon: "💻",
      description: "Console Avançado para Especialistas",
      color: "orange",
    },
    {
      id: "admin",
      label: "ADMINISTRAÇÃO",
      icon: "⚙️",
      description: "Monitoramento e Configurações",
      color: "yellow",
    },
  ];

  const getColorClasses = (color, isActive) => {
    const colors = {
      green: {
        active: "bg-green-500 text-black border-green-400",
        inactive:
          "bg-green-500/10 text-green-400 border-green-400/30 hover:bg-green-500/20 hover:border-green-400",
      },
      cyan: {
        active: "bg-red-500 text-black border-red-400",
        inactive:
          "bg-red-500/10 text-red-400 border-red-400/30 hover:bg-red-500/20 hover:border-red-400",
      },
      purple: {
        active: "bg-red-500 text-white border-red-400",
        inactive:
          "bg-red-500/10 text-red-400 border-red-400/30 hover:bg-red-500/20 hover:border-red-400",
      },
      orange: {
        active: "bg-orange-500 text-white border-orange-400",
        inactive:
          "bg-orange-500/10 text-orange-400 border-orange-400/30 hover:bg-orange-500/20 hover:border-orange-400",
      },
      yellow: {
        active: "bg-yellow-500 text-black border-yellow-400",
        inactive:
          "bg-yellow-500/10 text-yellow-400 border-yellow-400/30 hover:bg-yellow-500/20 hover:border-yellow-400",
      },
    };
    return colors[color][isActive ? "active" : "inactive"];
  };

  return (
    <header className="relative border-b border-green-400/30 bg-black/50 backdrop-blur-sm">
      {/* Logo e Info Principal */}
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 border-2 border-green-400 rounded-lg flex items-center justify-center bg-green-400/10">
            <span className="text-green-400 font-bold text-xl">V</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-green-400 tracking-wider">
              PROJETO VÉRTICE
            </h1>
            <p className="text-green-400/70 text-sm tracking-widest">
              SISTEMA DE INTELIGÊNCIA CRIMINAL
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Theme Selector */}
          <ThemeSelector compact={true} />

          {/* Clock */}
          <div className="text-right">
            <div className="text-green-400 font-bold text-lg">
              {formatTime(currentTime, "--:--:--")}
            </div>
            <div className="text-green-400/70 text-sm">
              {formatDate(currentTime, { dateStyle: "short" }, "N/A")}
            </div>
          </div>
        </div>
      </div>

      {/* Navegação Principal dos Módulos */}
      <nav
        className="px-4 py-3 bg-gradient-to-r from-gray-900/50 to-black/50 border-t border-green-400/20"
        role="navigation"
        aria-label="Módulos do Sistema"
      >
        <div className="flex items-center justify-center space-x-3 flex-wrap gap-y-2">
          <span className="text-green-400/70 text-xs font-bold tracking-widest mr-4">
            MÓDULOS DO SISTEMA:
          </span>
          {navigationModules.map((module) => (
            <button
              key={module.id}
              onClick={() => setCurrentView(module.id)}
              className={`
                flex items-center space-x-2 px-4 py-2 rounded-lg border transition-all duration-300 transform
                focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-black
                ${getColorClasses(module.color, currentView === module.id)}
                ${currentView === module.id ? "scale-105 shadow-lg focus:ring-current" : "hover:scale-102 focus:ring-white/50"}
              `}
              title={module.description}
              aria-label={`${module.label}: ${module.description}`}
              aria-current={currentView === module.id ? "page" : undefined}
            >
              <span className="text-lg" aria-hidden="true">
                {module.icon}
              </span>
              <div className="text-left">
                <div className="font-bold text-xs tracking-wider">
                  {module.label}
                </div>
                <div className="text-xs opacity-80 leading-tight hidden sm:block">
                  {module.description}
                </div>
              </div>
            </button>
          ))}
        </div>
      </nav>

      {/* Barra de Consulta (apenas no módulo principal) */}
      {currentView === "main" && (
        <div className="p-4 bg-gradient-to-r from-green-900/20 to-orange-900/20">
          <div className="flex items-center space-x-4">
            <div className="flex-1 relative">
              {/* Boris Cherny Standard - WCAG 2.1 AAA: Input Label (GAP #24) */}
              <label htmlFor="vehicle-plate-input" className="sr-only">
                Vehicle Plate
              </label>
              <input
                id="vehicle-plate-input"
                type="text"
                value={placa}
                onChange={(e) => setPlaca(e.target.value.toUpperCase())}
                onKeyPress={handleKeyPress}
                placeholder=">>> INSERIR PLACA DO VEÍCULO"
                aria-label="Vehicle plate number"
                className="w-full bg-black/70 border border-green-400/50 text-green-400 placeholder-green-400/50 p-3 rounded-lg focus:border-green-400 focus:outline-none focus:ring-2 focus:ring-green-400/50"
                disabled={loading}
              />
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                {loading && (
                  <div
                    className="w-6 h-6 border-2 border-green-400 border-t-transparent rounded-full animate-spin"
                    role="status"
                    aria-live="polite"
                    aria-label="Processing vehicle search"
                  ></div>
                )}
              </div>
            </div>

            <button
              onClick={handleSearch}
              disabled={loading || !placa.trim()}
              className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-500 hover:to-green-600 disabled:from-gray-600 disabled:to-gray-700 text-black font-bold px-8 py-3 rounded-lg transition-all duration-200"
            >
              {loading ? "PROCESSANDO..." : "EXECUTAR CONSULTA"}
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
      )}
    </header>
  );
};

export default Header;
