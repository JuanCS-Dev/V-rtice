// /home/juan/vertice-dev/frontend/src/components/AdminDashboard.jsx

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import SystemSelfCheck from './admin/SystemSelfCheck';
import { HITLConsole } from './admin/HITLConsole';
import SkipLink from './shared/SkipLink';
import { Breadcrumb } from './shared/Breadcrumb';
import useKeyboardNavigation from '../hooks/useKeyboardNavigation';
import { useClock } from '../hooks/useClock';
import { useAdminMetrics } from '../hooks/useAdminMetrics';
import { useSystemAlerts } from '../hooks/useSystemAlerts';

const AdminDashboard = ({ setCurrentView }) => {
  const { t } = useTranslation();
  const [activeModule, setActiveModule] = useState('overview');

  // Custom hooks
  const currentTime = useClock();
  const { metrics, loading } = useAdminMetrics();
  const systemAlerts = useSystemAlerts(t);

  const modules = [
    { id: 'overview', name: t('dashboard.admin.modules.overview'), icon: '📊' },
    { id: 'metrics', name: t('dashboard.admin.modules.metrics'), icon: '📈' },
    { id: 'security', name: t('dashboard.admin.modules.security'), icon: '🛡️' },
    { id: 'logs', name: t('dashboard.admin.modules.logs'), icon: '📋' },
    { id: 'hitl', name: t('dashboard.admin.modules.hitl', 'HITL'), icon: '🛡️' }
  ];

  const { getItemProps } = useKeyboardNavigation({
    itemCount: modules.length,
    onSelect: (index) => setActiveModule(modules[index].id),
    orientation: 'horizontal',
    loop: true
  });

  const renderModuleContent = () => {
    switch (activeModule) {
      case 'security':
        return <SystemSelfCheck />;
      case 'metrics':
        return <MetricsDetailedView metrics={metrics} loading={loading} />;
      case 'logs':
        return <SystemLogsView alerts={systemAlerts} />;
      case 'hitl':
        return <HITLConsole />;
      default:
        return <OverviewModule metrics={metrics} loading={loading} alerts={systemAlerts} />;
    }
  };

  return (
    <div className="h-screen w-screen bg-gradient-to-br from-gray-900 via-black to-gray-800 text-yellow-400 font-mono overflow-hidden flex flex-col">
      <SkipLink href="#main-content">{t('accessibility.skipToMain')}</SkipLink>

      {/* Scan Line */}
      <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-yellow-400 to-transparent animate-pulse z-20"></div>

      {/* Header */}
      <header className="relative border-b border-yellow-400/30 bg-black/50 backdrop-blur-sm">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 border-2 border-yellow-400 rounded-lg flex items-center justify-center bg-yellow-400/10">
              <span className="text-yellow-400 font-bold text-xl">A</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-yellow-400 tracking-wider">
                {t('dashboard.admin.title')}
              </h1>
              <p className="text-yellow-400/70 text-sm tracking-widest">{t('dashboard.admin.subtitle')}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setCurrentView('main')}
              className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-500 hover:to-green-600 text-black font-bold px-6 py-2 rounded-lg transition-all duration-300 tracking-wider focus:outline-none focus:ring-2 focus:ring-green-400"
              aria-label={t('navigation.back_to_hub')}
            >
              ← {t('common.back').toUpperCase()}
            </button>
            
            <div className="text-right">
              <div className="text-yellow-400 font-bold text-lg">
                {currentTime.toLocaleTimeString()}
              </div>
              <div className="text-yellow-400/70 text-sm">
                {currentTime.toLocaleDateString('pt-BR')}
              </div>
            </div>
          </div>
        </div>

        {/* Breadcrumb Navigation */}
        <div className="px-4 py-2 bg-gradient-to-r from-black/50 to-yellow-900/20 border-t border-yellow-400/10">
          <Breadcrumb
            items={[
              { label: 'VÉRTICE', icon: '🏠', onClick: () => setCurrentView('main') },
              { label: 'ADMINISTRAÇÃO', icon: '⚙️' },
              { label: modules.find(m => m.id === activeModule)?.name.toUpperCase() || 'OVERVIEW', icon: modules.find(m => m.id === activeModule)?.icon }
            ]}
            className="text-yellow-400"
          />
        </div>

        {/* Navigation Modules */}
        <div className="p-4 bg-gradient-to-r from-yellow-900/20 to-orange-900/20">
          <div className="flex space-x-2" role="tablist">
            {modules.map((module, index) => (
              <button
                key={module.id}
                {...getItemProps(index, {
                  onClick: () => setActiveModule(module.id),
                  role: 'tab',
                  'aria-selected': activeModule === module.id,
                  'aria-controls': `panel-${module.id}`,
                  className: `px-4 py-2 rounded-lg font-bold text-xs tracking-wider transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-yellow-400/50 ${
                    activeModule === module.id
                      ? 'bg-yellow-400/20 text-yellow-400 border border-yellow-400/50'
                      : 'bg-black/30 text-yellow-400/70 border border-yellow-400/20 hover:bg-yellow-400/10 hover:text-yellow-400'
                  }`
                })}
              >
                <span className="mr-2" aria-hidden="true">{module.icon}</span>
                {module.name}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main 
        id="main-content" 
        className="flex-1 p-6 overflow-hidden"
        role="tabpanel"
        aria-labelledby={`tab-${activeModule}`}
      >
        {renderModuleContent()}
      </main>

      {/* Footer */}
      <footer className="border-t border-yellow-400/30 bg-black/50 backdrop-blur-sm p-2">
        <div className="flex justify-between items-center text-xs">
          <div className="flex space-x-6">
            <span className="text-yellow-400">{t('dashboard.admin.footer.system')}: VÉRTICE v2.0</span>
            <span className="text-yellow-400">{t('dashboard.admin.footer.uptime')}: 99.8%</span>
            <span className="text-yellow-400">{t('dashboard.admin.footer.user')}: ADMIN_001</span>
            <span className="text-yellow-400">{t('dashboard.admin.footer.alerts')}: {systemAlerts.length}</span>
          </div>
          <div className="text-yellow-400/70">
            {t('dashboard.admin.footer.notice')}
          </div>
        </div>
      </footer>
    </div>
  );
};

// Componente Overview Expandido
const OverviewModule = ({ metrics, loading, alerts }) => {
  return (
    <div className="space-y-6">
      {/* Métricas Principais */}
      <div className="grid grid-cols-4 gap-6">
        <div className="bg-black/50 border border-yellow-400/50 rounded-lg p-6 backdrop-blur-sm">
          <h3 className="text-yellow-400/70 text-sm font-bold uppercase tracking-wider">Total de Consultas</h3>
          <p className="text-4xl font-bold text-green-400 mt-2">
            {loading ? '...' : Math.round(metrics.totalRequests).toLocaleString()}
          </p>
          <div className="text-xs text-yellow-400/50 mt-1">Desde o último reinício</div>
        </div>
        
        <div className="bg-black/50 border border-yellow-400/50 rounded-lg p-6 backdrop-blur-sm">
          <h3 className="text-yellow-400/70 text-sm font-bold uppercase tracking-wider">Latência Média</h3>
          <p className="text-4xl font-bold text-blue-400 mt-2">
            {loading ? '...' : `${metrics.averageLatency}ms`}
          </p>
          <div className={`text-xs mt-1 ${metrics.averageLatency > 500 ? 'text-red-400' : 'text-green-400'}`}>
            {metrics.averageLatency > 500 ? 'Acima do limite' : 'Dentro do normal'}
          </div>
        </div>
        
        <div className="bg-black/50 border border-yellow-400/50 rounded-lg p-6 backdrop-blur-sm">
          <h3 className="text-yellow-400/70 text-sm font-bold uppercase tracking-wider">Taxa de Erros</h3>
          <p className="text-4xl font-bold text-red-400 mt-2">
            {loading ? '...' : `${metrics.errorRate}%`}
          </p>
          <div className={`text-xs mt-1 ${parseFloat(metrics.errorRate) > 5 ? 'text-red-400' : 'text-green-400'}`}>
            {parseFloat(metrics.errorRate) > 5 ? 'Requer atenção' : 'Funcionando bem'}
          </div>
        </div>

        <div className="bg-black/50 border border-yellow-400/50 rounded-lg p-6 backdrop-blur-sm">
          <h3 className="text-yellow-400/70 text-sm font-bold uppercase tracking-wider">Status Geral</h3>
          <p className="text-4xl font-bold text-green-400 mt-2">
            {parseFloat(metrics.errorRate) < 5 && metrics.averageLatency < 500 ? '✓' : '⚠'}
          </p>
          <div className="text-xs text-yellow-400/50 mt-1">Sistema operacional</div>
        </div>
      </div>

      {/* Status dos Serviços */}
      <div className="border border-yellow-400/30 rounded-lg bg-black/20 backdrop-blur-sm p-6">
        <h3 className="text-yellow-400 font-bold text-xl mb-4 tracking-wider">STATUS DOS SERVIÇOS</h3>
        <div className="grid grid-cols-3 gap-4">
          <ServiceStatus name="API Gateway" status="online" port="8000" />
          <ServiceStatus name="SINESP Service" status="online" port="8001" />
          <ServiceStatus name="Database" status="online" port="5432" />
          <ServiceStatus name="Redis Cache" status="online" port="6379" />
          <ServiceStatus name="Frontend" status="online" port="5173" />
          <ServiceStatus name="Cyber Module" status="standby" port="8002" />
        </div>
      </div>

      {/* Alertas Recentes */}
      <div className="border border-yellow-400/30 rounded-lg bg-black/20 backdrop-blur-sm p-6">
        <h3 className="text-yellow-400 font-bold text-xl mb-4 tracking-wider">ALERTAS RECENTES</h3>
        <div className="space-y-2 max-h-60 overflow-y-auto">
          {alerts.length === 0 ? (
            <div className="text-center py-8 text-yellow-400/50">
              <div className="text-4xl mb-2">✅</div>
              <p>Nenhum alerta no sistema</p>
            </div>
          ) : (
            alerts.map((alert) => (
              <AlertItem key={alert.id} alert={alert} />
            ))
          )}
        </div>
      </div>
    </div>
  );
};

// Componente de Status de Serviço
const ServiceStatus = ({ name, status, port }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'online': return 'text-green-400 border-green-400';
      case 'standby': return 'text-yellow-400 border-yellow-400';
      case 'offline': return 'text-red-400 border-red-400';
      default: return 'text-gray-400 border-gray-400';
    }
  };

  return (
    <div className={`bg-black/40 border rounded p-3 ${getStatusColor(status)}`}>
      <div className="flex justify-between items-center">
        <span className="font-bold">{name}</span>
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${status === 'online' ? 'bg-green-400 animate-pulse' : status === 'standby' ? 'bg-yellow-400' : 'bg-red-400'}`}></div>
          <span className="text-xs uppercase">{status}</span>
        </div>
      </div>
      <div className="text-xs opacity-70 mt-1">Porta: {port}</div>
    </div>
  );
};

// Componente de Item de Alerta
const AlertItem = ({ alert }) => {
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'border-red-400 bg-red-400/10 text-red-400';
      case 'high': return 'border-orange-400 bg-orange-400/10 text-orange-400';
      case 'medium': return 'border-yellow-400 bg-yellow-400/10 text-yellow-400';
      case 'info': return 'border-blue-400 bg-blue-400/10 text-blue-400';
      default: return 'border-gray-400 bg-gray-400/10 text-gray-400';
    }
  };

  return (
    <div className={`p-3 rounded border-l-4 ${getSeverityColor(alert.severity)}`}>
      <div className="flex justify-between items-start">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-semibold px-2 py-1 rounded bg-black/50">{alert.type}</span>
          <span className="text-xs opacity-70">{alert.timestamp}</span>
        </div>
        <span className="text-xs font-bold uppercase">{alert.severity}</span>
      </div>
      <p className="text-sm mt-1">{alert.message}</p>
    </div>
  );
};

// Vista Detalhada de Métricas
const MetricsDetailedView = ({ metrics }) => {
  return (
    <div className="space-y-6">
      <div className="border border-yellow-400/50 rounded-lg bg-yellow-400/5 p-6">
        <h2 className="text-yellow-400 font-bold text-2xl mb-6 tracking-wider">MÉTRICAS DETALHADAS</h2>
        
        <div className="grid grid-cols-2 gap-8">
          {/* Performance Metrics */}
          <div className="space-y-4">
            <h3 className="text-yellow-400 font-bold text-lg">PERFORMANCE</h3>
            <div className="space-y-3">
              <MetricBar label="CPU Usage" value={Math.floor(Math.random() * 100)} unit="%" />
              <MetricBar label="Memory Usage" value={Math.floor(Math.random() * 100)} unit="%" />
              <MetricBar label="Disk I/O" value={Math.floor(Math.random() * 100)} unit="MB/s" />
              <MetricBar label="Network I/O" value={Math.floor(Math.random() * 100)} unit="KB/s" />
            </div>
          </div>

          {/* API Metrics */}
          <div className="space-y-4">
            <h3 className="text-yellow-400 font-bold text-lg">APIs & SERVIÇOS</h3>
            <div className="space-y-3">
              <div className="bg-black/30 border border-yellow-400/20 rounded p-3">
                <div className="flex justify-between">
                  <span className="text-yellow-400/70">Consultas SINESP</span>
                  <span className="text-yellow-400">{metrics.totalRequests}</span>
                </div>
              </div>
              <div className="bg-black/30 border border-yellow-400/20 rounded p-3">
                <div className="flex justify-between">
                  <span className="text-yellow-400/70">Cache Hit Rate</span>
                  <span className="text-green-400">94.2%</span>
                </div>
              </div>
              <div className="bg-black/30 border border-yellow-400/20 rounded p-3">
                <div className="flex justify-between">
                  <span className="text-yellow-400/70">Database Connections</span>
                  <span className="text-yellow-400">12/20</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Gráfico de Performance (Simulado) */}
      <div className="border border-yellow-400/30 rounded-lg bg-black/20 p-6">
        <h3 className="text-yellow-400 font-bold text-lg mb-4">GRÁFICO DE PERFORMANCE (24H)</h3>
        <div className="bg-black/40 rounded h-48 flex items-end justify-around p-4">
          {Array.from({ length: 24 }, (_, i) => {
            const randomHeight = Math.random() * 80 + 20;
            return (
              <div
                key={i}
                className="bg-yellow-400/50 w-4 rounded-t"
                style={{ '--bar-height': `${randomHeight}%`, height: 'var(--bar-height)' }}
                title={`${i}:00 - ${Math.floor(Math.random() * 100)}ms`}
              ></div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

// Componente de Barra de Métrica
const MetricBar = ({ label, value, unit }) => {
  const getColor = (value) => {
    if (value > 80) return 'bg-red-400';
    if (value > 60) return 'bg-orange-400';
    return 'bg-green-400';
  };

  return (
    <div className="bg-black/30 border border-yellow-400/20 rounded p-3">
      <div className="flex justify-between mb-2">
        <span className="text-yellow-400/70 text-sm">{label}</span>
        <span className="text-yellow-400 text-sm">{value}{unit}</span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-2">
        <div 
          className={`h-2 rounded-full ${getColor(value)}`}
          style={{ '--progress-width': `${value}%`, width: 'var(--progress-width)' }}
        ></div>
      </div>
    </div>
  );
};

// Vista de Logs do Sistema
const SystemLogsView = () => {
  const [logFilter, setLogFilter] = useState('all');
  
  const logEntries = [
    { time: '14:32:15', level: 'INFO', source: 'API_GATEWAY', message: 'Nova consulta processada: ABC1234' },
    { time: '14:31:58', level: 'DEBUG', source: 'SINESP_SERVICE', message: 'Cache miss - consultando API externa' },
    { time: '14:31:45', level: 'WARN', source: 'DATABASE', message: 'Query lenta detectada: 850ms' },
    { time: '14:30:22', level: 'ERROR', source: 'EXTERNAL_API', message: 'Timeout na consulta DETRAN' },
    { time: '14:29:33', level: 'INFO', source: 'SYSTEM', message: 'Backup automático iniciado' }
  ];

  return (
    <div className="space-y-6">
      <div className="border border-yellow-400/50 rounded-lg bg-yellow-400/5 p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-yellow-400 font-bold text-2xl tracking-wider">LOGS DO SISTEMA</h2>
          <select 
            value={logFilter}
            onChange={(e) => setLogFilter(e.target.value)}
            className="bg-black/70 border border-yellow-400/50 text-yellow-400 p-2 rounded font-mono text-sm"
          >
            <option value="all">Todos os Logs</option>
            <option value="error">Apenas Erros</option>
            <option value="warn">Avisos</option>
            <option value="info">Informações</option>
          </select>
        </div>

        <div className="bg-black/40 rounded p-4 h-96 overflow-y-auto font-mono text-sm">
          {logEntries.map((entry, index) => (
            <div key={index} className="flex space-x-4 py-1 border-b border-yellow-400/10">
              <span className="text-yellow-400/50">{entry.time}</span>
              <span className={`w-12 ${
                entry.level === 'ERROR' ? 'text-red-400' :
                entry.level === 'WARN' ? 'text-orange-400' :
                entry.level === 'INFO' ? 'text-blue-400' :
                'text-gray-400'
              }`}>
                {entry.level}
              </span>
              <span className="text-yellow-400/70 w-24">{entry.source}</span>
              <span className="text-yellow-400 flex-1">{entry.message}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Ações de Manutenção */}
      <div className="border border-yellow-400/30 rounded-lg bg-black/20 p-6">
        <h3 className="text-yellow-400 font-bold text-lg mb-4">AÇÕES DE MANUTENÇÃO</h3>
        <div className="grid grid-cols-4 gap-4">
          <button className="bg-gradient-to-r from-blue-600 to-blue-700 text-white font-bold py-3 px-4 rounded hover:from-blue-500 hover:to-blue-600 transition-all">
            EXPORTAR LOGS
          </button>
          <button className="bg-gradient-to-r from-orange-600 to-orange-700 text-white font-bold py-3 px-4 rounded hover:from-orange-500 hover:to-orange-600 transition-all">
            LIMPAR CACHE
          </button>
          <button className="bg-gradient-to-r from-purple-600 to-purple-700 text-white font-bold py-3 px-4 rounded hover:from-purple-500 hover:to-purple-600 transition-all">
            BACKUP MANUAL
          </button>
          <button className="bg-gradient-to-r from-red-600 to-red-700 text-white font-bold py-3 px-4 rounded hover:from-red-500 hover:to-red-600 transition-all">
            REINICIAR SERVIÇOS
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
