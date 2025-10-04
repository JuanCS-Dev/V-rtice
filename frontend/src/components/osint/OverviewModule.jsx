/**
 * OverviewModule - OSINT Operations Overview
 *
 * Displays OSINT operations center with:
 * - Key metrics (investigations, targets, threats, data points)
 * - Module status grid
 * - Real-time activity indicators
 *
 * @param {Object} stats - System statistics object
 */

import React from 'react';
import PropTypes from 'prop-types';
import { ModuleStatusCard } from '../shared/widgets';

const OSINT_MODULES = [
  { name: 'Maximus AI Engine', status: 'online', activity: 'Analisando padrões' },
  { name: 'Username Hunter', status: 'online', activity: 'Monitorando 2,847 perfis' },
  { name: 'Email Analyzer', status: 'online', activity: 'Verificando 1,293 emails' },
  { name: 'Phone Intelligence', status: 'online', activity: 'Rastreando 847 números' },
  { name: 'Social Scraper', status: 'online', activity: 'Coletando dados em tempo real' },
  { name: 'Dark Web Monitor', status: 'online', activity: 'Varredura profunda ativa' }
];

export const OverviewModule = ({ stats }) => {
  return (
    <div className="space-y-6">
      <div className="border border-purple-400/50 rounded-lg bg-purple-400/5 p-6">
        <h2 className="text-purple-400 font-bold text-2xl mb-6 tracking-wider">
          CENTRO DE OPERAÇÕES OSINT
        </h2>

        {/* Métricas Principais */}
        <div className="grid grid-cols-4 gap-6 mb-8">
          <div className="bg-black/50 border border-red-400/50 rounded-lg p-4 text-center">
            <div className="text-red-400 text-3xl font-bold">{stats.totalInvestigations}</div>
            <div className="text-red-400/70 text-sm">INVESTIGAÇÕES TOTAIS</div>
          </div>
          <div className="bg-black/50 border border-yellow-400/50 rounded-lg p-4 text-center">
            <div className="text-yellow-400 text-3xl font-bold">{stats.activeTargets}</div>
            <div className="text-yellow-400/70 text-sm">ALVOS ATIVOS</div>
          </div>
          <div className="bg-black/50 border border-orange-400/50 rounded-lg p-4 text-center">
            <div className="text-orange-400 text-3xl font-bold">{stats.threatsDetected}</div>
            <div className="text-orange-400/70 text-sm">AMEAÇAS DETECTADAS</div>
          </div>
          <div className="bg-black/50 border border-purple-400/50 rounded-lg p-4 text-center">
            <div className="text-purple-400 text-3xl font-bold">{stats.dataPoints}K</div>
            <div className="text-purple-400/70 text-sm">PONTOS DE DADOS</div>
          </div>
        </div>

        {/* Status dos Módulos OSINT */}
        <div className="space-y-4">
          <h3 className="text-purple-400 font-bold text-lg mb-4">STATUS DOS MÓDULOS OSINT</h3>
          <div className="grid grid-cols-3 gap-4">
            {OSINT_MODULES.map((module, idx) => (
              <ModuleStatusCard
                key={idx}
                name={module.name}
                status={module.status}
                activity={module.activity}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

OverviewModule.propTypes = {
  stats: PropTypes.shape({
    totalInvestigations: PropTypes.number.isRequired,
    activeTargets: PropTypes.number.isRequired,
    threatsDetected: PropTypes.number.isRequired,
    dataPoints: PropTypes.number.isRequired
  }).isRequired
};

export default OverviewModule;
