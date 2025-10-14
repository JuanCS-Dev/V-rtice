// /home/juan/vertice-dev/frontend/src/components/AdminDashboard.jsx

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import SystemSelfCheck from './admin/SystemSelfCheck';
import { HITLConsole } from './admin/HITLConsole';
import { AdminHeader } from './admin/AdminHeader';
import SkipLink from './shared/SkipLink';
import { DashboardFooter } from './shared/DashboardFooter';
import useKeyboardNavigation from '../hooks/useKeyboardNavigation';
import { useClock } from '../hooks/useClock';
import { useAdminMetrics } from '../hooks/useAdminMetrics';
import { useSystemAlerts } from '../hooks/useSystemAlerts';
import styles from './AdminDashboard.module.css';

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
    <div className={styles.dashboard}>
      <SkipLink href="#main-content">{t('accessibility.skipToMain')}</SkipLink>

      {/* Scan Line */}
      <div className={styles.scanLine}></div>

      {/* Header */}
      <AdminHeader
        currentTime={currentTime}
        activeModule={activeModule}
        modules={modules}
        setActiveModule={setActiveModule}
        setCurrentView={setCurrentView}
        getItemProps={getItemProps}
      />

      {/* Main Content */}
      <main
        id="main-content"
        className={styles.mainContent}
        role="tabpanel"
        aria-labelledby={`tab-${activeModule}`}
      >
        {renderModuleContent()}
      </main>

      {/* Footer */}
      <DashboardFooter
        moduleName="ADMIN CONTROL"
        classification="RESTRITO"
        statusItems={[
          { label: 'SYSTEM', value: 'VÉRTICE v2.0', online: true },
          { label: 'USER', value: 'ADMIN_001', online: true }
        ]}
        metricsItems={[
          { label: 'UPTIME', value: '99.8%' },
          { label: 'ALERTS', value: systemAlerts.length }
        ]}
        showTimestamp={true}
      />
    </div>
  );
};

// Componente Overview Expandido
const OverviewModule = ({ metrics, loading, alerts }) => {
  return (
    <div className={styles.overviewContainer}>
      {/* Métricas Principais */}
      <div className={styles.metricsGrid}>
        <div className={styles.metricCard}>
          <h3 className={styles.metricLabel}>Total de Consultas</h3>
          <p className={`${styles.metricValue} ${styles.success}`}>
            {loading ? '...' : Math.round(metrics.totalRequests).toLocaleString()}
          </p>
          <div className={styles.metricSubtext}>Desde o último reinício</div>
        </div>

        <div className={styles.metricCard}>
          <h3 className={styles.metricLabel}>Latência Média</h3>
          <p className={`${styles.metricValue} ${styles.warning}`}>
            {loading ? '...' : `${metrics.averageLatency}ms`}
          </p>
          <div className={`${styles.metricSubtext} ${metrics.averageLatency > 500 ? styles.error : styles.success}`}>
            {metrics.averageLatency > 500 ? 'Acima do limite' : 'Dentro do normal'}
          </div>
        </div>

        <div className={styles.metricCard}>
          <h3 className={styles.metricLabel}>Taxa de Erros</h3>
          <p className={`${styles.metricValue} ${styles.error}`}>
            {loading ? '...' : `${metrics.errorRate}%`}
          </p>
          <div className={`${styles.metricSubtext} ${parseFloat(metrics.errorRate) > 5 ? styles.error : styles.success}`}>
            {parseFloat(metrics.errorRate) > 5 ? 'Requer atenção' : 'Funcionando bem'}
          </div>
        </div>

        <div className={styles.metricCard}>
          <h3 className={styles.metricLabel}>Status Geral</h3>
          <p className={`${styles.metricValue} ${styles.success}`}>
            {parseFloat(metrics.errorRate) < 5 && metrics.averageLatency < 500 ? '✓' : '⚠'}
          </p>
          <div className={styles.metricSubtext}>Sistema operacional</div>
        </div>
      </div>

      {/* Status dos Serviços */}
      <div className={styles.sectionCard}>
        <h3 className={styles.sectionTitle}>STATUS DOS SERVIÇOS</h3>
        <div className={styles.servicesGrid}>
          <ServiceStatus name="API Gateway" status="online" port="8000" />
          <ServiceStatus name="SINESP Service" status="online" port="8001" />
          <ServiceStatus name="Database" status="online" port="5432" />
          <ServiceStatus name="Redis Cache" status="online" port="6379" />
          <ServiceStatus name="Frontend" status="online" port="5173" />
          <ServiceStatus name="Cyber Module" status="standby" port="8002" />
        </div>
      </div>

      {/* Alertas Recentes */}
      <div className={styles.sectionCard}>
        <h3 className={styles.sectionTitle}>ALERTAS RECENTES</h3>
        <div className={styles.alertsList}>
          {alerts.length === 0 ? (
            <div className={styles.alertsEmpty}>
              <div className={styles.alertsEmptyIcon}>✅</div>
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
  return (
    <div className={`${styles.serviceCard} ${styles[status]}`}>
      <div className={styles.serviceHeader}>
        <span className={styles.serviceName}>{name}</span>
        <div className={styles.serviceStatus}>
          <div className={`${styles.statusDot} ${styles[status]}`}></div>
          <span className={styles.statusLabel}>{status}</span>
        </div>
      </div>
      <div className={styles.servicePort}>Porta: {port}</div>
    </div>
  );
};

// Componente de Item de Alerta
const AlertItem = ({ alert }) => {
  return (
    <div className={`${styles.alertItem} ${styles[alert.severity]}`}>
      <div className={styles.alertHeader}>
        <div className={styles.alertMeta}>
          <span className={styles.alertType}>{alert.type}</span>
          <span className={styles.alertTimestamp}>{alert.timestamp}</span>
        </div>
        <span className={styles.alertSeverity}>{alert.severity}</span>
      </div>
      <p className={styles.alertMessage}>{alert.message}</p>
    </div>
  );
};

// Vista Detalhada de Métricas
const MetricsDetailedView = ({ metrics }) => {
  return (
    <div className={styles.metricsDetailed}>
      <div className={styles.metricsCard}>
        <h2 className={styles.metricsTitle}>MÉTRICAS DETALHADAS</h2>

        <div className={styles.metricsColumns}>
          {/* Performance Metrics */}
          <div className={styles.metricsSection}>
            <h3 className={styles.metricsSectionTitle}>PERFORMANCE</h3>
            <div>
              <MetricBar label="CPU Usage" value={Math.floor(Math.random() * 100)} unit="%" />
              <MetricBar label="Memory Usage" value={Math.floor(Math.random() * 100)} unit="%" />
              <MetricBar label="Disk I/O" value={Math.floor(Math.random() * 100)} unit="MB/s" />
              <MetricBar label="Network I/O" value={Math.floor(Math.random() * 100)} unit="KB/s" />
            </div>
          </div>

          {/* API Metrics */}
          <div className={styles.metricsSection}>
            <h3 className={styles.metricsSectionTitle}>APIs & SERVIÇOS</h3>
            <div className={styles.apiMetricsList}>
              <div className={styles.apiMetricItem}>
                <div className={styles.apiMetricRow}>
                  <span className={styles.apiMetricLabel}>Consultas SINESP</span>
                  <span className={styles.apiMetricValue}>{metrics.totalRequests}</span>
                </div>
              </div>
              <div className={styles.apiMetricItem}>
                <div className={styles.apiMetricRow}>
                  <span className={styles.apiMetricLabel}>Cache Hit Rate</span>
                  <span className={`${styles.apiMetricValue} ${styles.success}`}>94.2%</span>
                </div>
              </div>
              <div className={styles.apiMetricItem}>
                <div className={styles.apiMetricRow}>
                  <span className={styles.apiMetricLabel}>Database Connections</span>
                  <span className={styles.apiMetricValue}>12/20</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Gráfico de Performance (Simulado) */}
      <div className={styles.chartContainer}>
        <h3 className={styles.chartTitle}>GRÁFICO DE PERFORMANCE (24H)</h3>
        <div className={styles.chartBars}>
          {Array.from({ length: 24 }, (_, i) => {
            const randomHeight = Math.random() * 80 + 20;
            return (
              <div
                key={i}
                className={styles.chartBar}
                style={{ height: `${randomHeight}%` }}
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
  const getColorClass = (value) => {
    if (value > 80) return styles.high;
    if (value > 60) return styles.medium;
    return styles.low;
  };

  return (
    <div className={styles.metricBarContainer}>
      <div className={styles.metricBarHeader}>
        <span className={styles.metricBarLabel}>{label}</span>
        <span className={styles.metricBarValue}>{value}{unit}</span>
      </div>
      <div className={styles.metricBarTrack}>
        <div
          className={`${styles.metricBarFill} ${getColorClass(value)}`}
          style={{ width: `${value}%` }}
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
    <div className={styles.logsContainer}>
      <div className={styles.logsCard}>
        <div className={styles.logsHeader}>
          <h2 className={styles.logsTitle}>LOGS DO SISTEMA</h2>
          <select
            value={logFilter}
            onChange={(e) => setLogFilter(e.target.value)}
            className={styles.logsFilter}
          >
            <option value="all">Todos os Logs</option>
            <option value="error">Apenas Erros</option>
            <option value="warn">Avisos</option>
            <option value="info">Informações</option>
          </select>
        </div>

        <div className={styles.logsViewer}>
          {logEntries.map((entry, index) => (
            <div key={index} className={styles.logEntry}>
              <span className={styles.logTime}>{entry.time}</span>
              <span className={`${styles.logLevel} ${styles[entry.level.toLowerCase()]}`}>
                {entry.level}
              </span>
              <span className={styles.logSource}>{entry.source}</span>
              <span className={styles.logMessage}>{entry.message}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Ações de Manutenção */}
      <div className={styles.actionsCard}>
        <h3 className={styles.actionsTitle}>AÇÕES DE MANUTENÇÃO</h3>
        <div className={styles.actionsGrid}>
          <button className={`${styles.actionButton} ${styles.export}`}>
            EXPORTAR LOGS
          </button>
          <button className={`${styles.actionButton} ${styles.clear}`}>
            LIMPAR CACHE
          </button>
          <button className={`${styles.actionButton} ${styles.backup}`}>
            BACKUP MANUAL
          </button>
          <button className={`${styles.actionButton} ${styles.restart}`}>
            REINICIAR SERVIÇOS
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
