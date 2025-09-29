import React, { useState, useEffect } from 'react';

const SystemSecurity = () => {
  const [securityData, setSecurityData] = useState({
    portAnalysis: null,
    fileIntegrity: null,
    processAnalysis: null,
    securityConfig: null,
    securityLogs: null
  });
  const [loading, setLoading] = useState({});
  const [lastUpdate, setLastUpdate] = useState(null);

  // Função para buscar dados de um endpoint específico
  const fetchSecurityData = async (endpoint, key) => {
    setLoading(prev => ({ ...prev, [key]: true }));
    try {
      const response = await fetch(`http://localhost:8000${endpoint}`);
      const data = await response.json();

      if (data.success) {
        setSecurityData(prev => ({ ...prev, [key]: data.data }));
      } else {
        console.error(`Erro em ${endpoint}:`, data.errors);
      }
    } catch (error) {
      console.error(`Erro ao buscar ${endpoint}:`, error);
    } finally {
      setLoading(prev => ({ ...prev, [key]: false }));
    }
  };

  // Carrega todos os dados de segurança
  const loadAllSecurityData = async () => {
    setLastUpdate(new Date());

    const endpoints = [
      { endpoint: '/cyber/port-analysis', key: 'portAnalysis' },
      { endpoint: '/cyber/file-integrity', key: 'fileIntegrity' },
      { endpoint: '/cyber/process-analysis', key: 'processAnalysis' },
      { endpoint: '/cyber/security-config', key: 'securityConfig' },
      { endpoint: '/cyber/security-logs', key: 'securityLogs' }
    ];

    // Executa todas as consultas em paralelo
    await Promise.all(
      endpoints.map(({ endpoint, key }) => fetchSecurityData(endpoint, key))
    );
  };

  // Carrega dados iniciais
  useEffect(() => {
    loadAllSecurityData();
  }, []);

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return 'text-red-400 border-red-400 bg-red-400/10';
      case 'high': return 'text-orange-400 border-orange-400 bg-orange-400/10';
      case 'medium': return 'text-yellow-400 border-yellow-400 bg-yellow-400/10';
      case 'low': return 'text-green-400 border-green-400 bg-green-400/10';
      default: return 'text-cyan-400 border-cyan-400 bg-cyan-400/10';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border border-cyan-400/50 rounded-lg bg-cyan-400/5 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-cyan-400 font-bold text-2xl tracking-wider">
              SYSTEM SECURITY ANALYSIS
            </h2>
            <p className="text-cyan-400/70 mt-1">Análise completa de segurança do sistema</p>
          </div>

          <button
            onClick={loadAllSecurityData}
            className="bg-gradient-to-r from-cyan-600 to-cyan-700 hover:from-cyan-500 hover:to-cyan-600 text-black font-bold px-6 py-3 rounded-lg transition-all duration-300 tracking-wider"
          >
            🔄 ATUALIZAR DADOS
          </button>
        </div>

        {lastUpdate && (
          <div className="text-cyan-400/70 text-sm">
            Última atualização: {lastUpdate.toLocaleTimeString('pt-BR')}
          </div>
        )}
      </div>

      {/* Análise de Portas */}
      <div className="border border-cyan-400/30 rounded-lg bg-black/20 p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-cyan-400 font-bold text-lg">🔍 ANÁLISE DE PORTAS</h3>
          {loading.portAnalysis && <div className="text-cyan-400">Carregando...</div>}
        </div>

        {securityData.portAnalysis ? (
          <div className="space-y-4">
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-black/50 border border-cyan-400/50 rounded p-3 text-center">
                <div className="text-cyan-400 text-xl font-bold">
                  {securityData.portAnalysis.total_listening || 0}
                </div>
                <div className="text-cyan-400/70 text-sm">PORTAS ABERTAS</div>
              </div>
              <div className="bg-black/50 border border-orange-400/50 rounded p-3 text-center">
                <div className="text-orange-400 text-xl font-bold">
                  {securityData.portAnalysis.suspicious_ports?.length || 0}
                </div>
                <div className="text-orange-400/70 text-sm">SUSPEITAS</div>
              </div>
              <div className="bg-black/50 border border-green-400/50 rounded p-3 text-center">
                <div className="text-green-400 text-xl font-bold">
                  {securityData.portAnalysis.total_connections || 0}
                </div>
                <div className="text-green-400/70 text-sm">CONEXÕES</div>
              </div>
              <div className="bg-black/50 border border-yellow-400/50 rounded p-3 text-center">
                <div className="text-yellow-400 text-xl font-bold">
                  {securityData.portAnalysis.listening_ports?.filter(p => [22, 80, 443, 8000].includes(p.port)).length || 0}
                </div>
                <div className="text-yellow-400/70 text-sm">ESSENCIAIS</div>
              </div>
            </div>

            {securityData.portAnalysis.suspicious_ports?.length > 0 && (
              <div>
                <h4 className="text-orange-400 font-bold mb-2">PORTAS SUSPEITAS</h4>
                <div className="space-y-2">
                  {securityData.portAnalysis.suspicious_ports.slice(0, 5).map((port, index) => (
                    <div key={index} className="bg-orange-400/10 border border-orange-400/30 rounded p-2">
                      <span className="text-orange-400 font-bold">Porta {port.port}</span>
                      <span className="text-orange-400/70 ml-2">
                        ({port.address}) - Processo: {port.process}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-cyan-400/70">
            Clique em "ATUALIZAR DADOS" para carregar análise de portas
          </div>
        )}
      </div>

      {/* Análise de Processos */}
      <div className="border border-cyan-400/30 rounded-lg bg-black/20 p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-cyan-400 font-bold text-lg">⚙️ ANÁLISE DE PROCESSOS</h3>
          {loading.processAnalysis && <div className="text-cyan-400">Carregando...</div>}
        </div>

        {securityData.processAnalysis ? (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-black/50 border border-cyan-400/50 rounded p-3 text-center">
                <div className="text-cyan-400 text-xl font-bold">
                  {securityData.processAnalysis.total_processes || 0}
                </div>
                <div className="text-cyan-400/70 text-sm">PROCESSOS TOTAIS</div>
              </div>
              <div className="bg-black/50 border border-green-400/50 rounded p-3 text-center">
                <div className="text-green-400 text-xl font-bold">
                  {securityData.processAnalysis.vertice_processes?.length || 0}
                </div>
                <div className="text-green-400/70 text-sm">VÉRTICE</div>
              </div>
              <div className="bg-black/50 border border-red-400/50 rounded p-3 text-center">
                <div className="text-red-400 text-xl font-bold">
                  {securityData.processAnalysis.suspicious_processes?.length || 0}
                </div>
                <div className="text-red-400/70 text-sm">SUSPEITOS</div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="text-cyan-400 font-bold mb-2">SISTEMA</h4>
                <div className="bg-black/30 border border-cyan-400/20 rounded p-3 text-sm">
                  <div>CPU: {securityData.processAnalysis.cpu_usage?.toFixed(1) || 0}%</div>
                  <div>Memória: {((securityData.processAnalysis.memory_usage?.percent || 0)).toFixed(1)}%</div>
                  {securityData.processAnalysis.system_load && (
                    <div>Load: {securityData.processAnalysis.system_load.join(', ')}</div>
                  )}
                </div>
              </div>

              {securityData.processAnalysis.suspicious_processes?.length > 0 && (
                <div>
                  <h4 className="text-red-400 font-bold mb-2">PROCESSOS SUSPEITOS</h4>
                  <div className="space-y-1">
                    {securityData.processAnalysis.suspicious_processes.slice(0, 3).map((proc, index) => (
                      <div key={index} className="bg-red-400/10 border border-red-400/30 rounded p-2 text-sm">
                        <span className="text-red-400 font-bold">{proc.name}</span>
                        <span className="text-red-400/70 ml-2">PID: {proc.pid}</span>
                        <div className="text-red-400/50 text-xs">{proc.reason}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-cyan-400/70">
            Aguardando dados de análise de processos...
          </div>
        )}
      </div>

      {/* Configuração de Segurança */}
      <div className="border border-cyan-400/30 rounded-lg bg-black/20 p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-cyan-400 font-bold text-lg">🔒 CONFIGURAÇÃO DE SEGURANÇA</h3>
          {loading.securityConfig && <div className="text-cyan-400">Carregando...</div>}
        </div>

        {securityData.securityConfig ? (
          <div className="grid grid-cols-3 gap-4">
            {/* Firewall */}
            <div className="bg-black/30 border border-cyan-400/20 rounded p-3">
              <h4 className="text-cyan-400 font-bold mb-2">FIREWALL</h4>
              {securityData.securityConfig.firewall ? (
                <div className="text-sm">
                  <div className={`inline-block px-2 py-1 rounded text-xs ${
                    securityData.securityConfig.firewall.ufw_active ?
                    'bg-green-400/20 text-green-400' : 'bg-red-400/20 text-red-400'
                  }`}>
                    {securityData.securityConfig.firewall.ufw_active ? 'ATIVO' : 'INATIVO'}
                  </div>
                </div>
              ) : (
                <div className="text-red-400 text-sm">Erro na verificação</div>
              )}
            </div>

            {/* SSH */}
            <div className="bg-black/30 border border-cyan-400/20 rounded p-3">
              <h4 className="text-cyan-400 font-bold mb-2">SSH</h4>
              {securityData.securityConfig.ssh ? (
                <div className="text-sm space-y-1">
                  <div className={`inline-block px-2 py-1 rounded text-xs ${
                    securityData.securityConfig.ssh.config_exists ?
                    'bg-green-400/20 text-green-400' : 'bg-red-400/20 text-red-400'
                  }`}>
                    {securityData.securityConfig.ssh.config_exists ? 'CONFIGURADO' : 'SEM CONFIG'}
                  </div>
                  {securityData.securityConfig.ssh.root_login !== undefined && (
                    <div className={`inline-block px-2 py-1 rounded text-xs ml-1 ${
                      !securityData.securityConfig.ssh.root_login ?
                      'bg-green-400/20 text-green-400' : 'bg-red-400/20 text-red-400'
                    }`}>
                      {!securityData.securityConfig.ssh.root_login ? 'ROOT NEGADO' : 'ROOT PERMITIDO'}
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-red-400 text-sm">Erro na verificação</div>
              )}
            </div>

            {/* Usuários */}
            <div className="bg-black/30 border border-cyan-400/20 rounded p-3">
              <h4 className="text-cyan-400 font-bold mb-2">USUÁRIOS</h4>
              {securityData.securityConfig.users ? (
                <div className="text-sm">
                  <div>Total: {securityData.securityConfig.users.total_users || 0}</div>
                  <div>Com Shell: {securityData.securityConfig.users.shell_users?.length || 0}</div>
                </div>
              ) : (
                <div className="text-red-400 text-sm">Erro na verificação</div>
              )}
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-cyan-400/70">
            Aguardando dados de configuração de segurança...
          </div>
        )}
      </div>

      {/* Logs de Segurança */}
      <div className="border border-cyan-400/30 rounded-lg bg-black/20 p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-cyan-400 font-bold text-lg">📋 LOGS DE SEGURANÇA</h3>
          {loading.securityLogs && <div className="text-cyan-400">Carregando...</div>}
        </div>

        {securityData.securityLogs ? (
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-black/30 border border-cyan-400/20 rounded p-3">
              <h4 className="text-red-400 font-bold mb-2">TENTATIVAS FALHADAS</h4>
              <div className="text-red-400 text-2xl font-bold mb-2">
                {securityData.securityLogs.failed_logins || 0}
              </div>
              {securityData.securityLogs.recent_failed?.length > 0 && (
                <div className="space-y-1">
                  {securityData.securityLogs.recent_failed.slice(0, 3).map((log, index) => (
                    <div key={index} className="text-xs text-red-400/70 font-mono truncate">
                      {log}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="bg-black/30 border border-cyan-400/20 rounded p-3">
              <h4 className="text-green-400 font-bold mb-2">LOGINS VÁLIDOS</h4>
              <div className="text-green-400 text-2xl font-bold mb-2">
                {securityData.securityLogs.successful_logins || 0}
              </div>
              {securityData.securityLogs.recent_successful?.length > 0 && (
                <div className="space-y-1">
                  {securityData.securityLogs.recent_successful.slice(0, 3).map((log, index) => (
                    <div key={index} className="text-xs text-green-400/70 font-mono truncate">
                      {log}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-cyan-400/70">
            Aguardando dados de logs de segurança...
          </div>
        )}
      </div>
    </div>
  );
};

export default SystemSecurity;