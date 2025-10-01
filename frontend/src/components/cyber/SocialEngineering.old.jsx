import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../../contexts/AuthContext';

const SocialEngineering = () => {
  const { user, getAuthToken } = useContext(AuthContext);
  const [socialEngData, setSocialEngData] = useState({
    campaigns: [],
    templates: [],
    activeCampaign: null
  });
  const [loading, setLoading] = useState({});
  const [campaignForm, setCampaignForm] = useState({
    name: '',
    template_id: '',
    target_emails: '',
    sender_name: '',
    sender_email: '',
    landing_page_url: ''
  });
  const [awarenessForm, setAwarenessForm] = useState({
    title: '',
    description: '',
    target_group: 'all',
    difficulty_level: 'medium'
  });

  // Verifica se o usuário tem permissão ofensiva
  const hasOffensivePermission = user?.permissions?.includes('offensive') || user?.email === 'juan.brainfarma@gmail.com';

  // Headers com autenticação
  const getHeaders = () => {
    const token = getAuthToken();
    return {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    };
  };

  // Carrega templates disponíveis
  const loadTemplates = async () => {
    if (!hasOffensivePermission) return;

    setLoading(prev => ({ ...prev, templates: true }));
    try {
      const response = await fetch('http://localhost:8000/api/social-eng/templates', {
        headers: getHeaders()
      });
      const data = await response.json();

      if (response.ok) {
        setSocialEngData(prev => ({ ...prev, templates: data.templates || [] }));
      } else {
        console.error('Erro ao carregar templates:', data.detail);
      }
    } catch (error) {
      console.error('Erro ao carregar templates:', error);
    } finally {
      setLoading(prev => ({ ...prev, templates: false }));
    }
  };

  // Cria campanha de phishing
  const createCampaign = async (e) => {
    e.preventDefault();
    if (!hasOffensivePermission) {
      alert('Permissão ofensiva necessária para criar campanhas');
      return;
    }

    setLoading(prev => ({ ...prev, campaign: true }));
    try {
      const emails = campaignForm.target_emails.split(',').map(email => email.trim());
      const campaignData = {
        ...campaignForm,
        target_emails: emails
      };

      const response = await fetch('http://localhost:8000/api/social-eng/campaign', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(campaignData)
      });
      const data = await response.json();

      if (response.ok) {
        setSocialEngData(prev => ({
          ...prev,
          activeCampaign: data,
          campaigns: [...prev.campaigns, data]
        }));
        setCampaignForm({
          name: '',
          template_id: '',
          target_emails: '',
          sender_name: '',
          sender_email: '',
          landing_page_url: ''
        });
        alert('Campanha criada com sucesso!');

        // Polling para atualizar status da campanha
        pollCampaignStatus(data.campaign_id);
      } else {
        alert(`Erro ao criar campanha: ${data.detail}`);
      }
    } catch (error) {
      console.error('Erro ao criar campanha:', error);
      alert('Erro ao criar campanha');
    } finally {
      setLoading(prev => ({ ...prev, campaign: false }));
    }
  };

  // Cria treinamento de conscientização
  const createAwarenessTraining = async (e) => {
    e.preventDefault();
    if (!hasOffensivePermission) {
      alert('Permissão ofensiva necessária para criar treinamentos');
      return;
    }

    setLoading(prev => ({ ...prev, awareness: true }));
    try {
      const response = await fetch('http://localhost:8000/api/social-eng/awareness', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(awarenessForm)
      });
      const data = await response.json();

      if (response.ok) {
        alert('Treinamento de conscientização criado com sucesso!');
        setAwarenessForm({
          title: '',
          description: '',
          target_group: 'all',
          difficulty_level: 'medium'
        });
      } else {
        alert(`Erro ao criar treinamento: ${data.detail}`);
      }
    } catch (error) {
      console.error('Erro ao criar treinamento:', error);
      alert('Erro ao criar treinamento');
    } finally {
      setLoading(prev => ({ ...prev, awareness: false }));
    }
  };

  // Polling para status da campanha
  const pollCampaignStatus = (campaignId) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/social-eng/campaign/${campaignId}`, {
          headers: getHeaders()
        });
        const data = await response.json();

        if (response.ok) {
          setSocialEngData(prev => ({ ...prev, activeCampaign: data }));

          if (data.status === 'completed' || data.status === 'failed') {
            clearInterval(interval);
          }
        }
      } catch (error) {
        console.error('Erro ao verificar status da campanha:', error);
        clearInterval(interval);
      }
    }, 5000);
  };

  // Busca analytics de uma campanha
  const getCampaignAnalytics = async (campaignId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/social-eng/analytics/${campaignId}`, {
        headers: getHeaders()
      });
      const data = await response.json();

      if (response.ok) {
        alert(`Analytics: ${JSON.stringify(data.analytics, null, 2)}`);
      }
    } catch (error) {
      console.error('Erro ao buscar analytics:', error);
    }
  };

  useEffect(() => {
    if (hasOffensivePermission) {
      loadTemplates();
    }
  }, [hasOffensivePermission]);

  if (!hasOffensivePermission) {
    return (
      <div className="bg-gray-900 p-6 rounded-lg">
        <div className="text-center">
          <div className="text-red-400 text-6xl mb-4">🔒</div>
          <h3 className="text-xl font-bold text-red-400 mb-2">Acesso Negado</h3>
          <p className="text-gray-400">
            Você não tem permissão para acessar ferramentas ofensivas.
            <br />
            Apenas usuários com permissão 'offensive' podem utilizar o Social Engineering Toolkit.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-900 to-pink-900 p-6 rounded-lg">
        <h2 className="text-2xl font-bold text-white mb-2">🎭 Social Engineering Toolkit</h2>
        <p className="text-purple-200">
          Ferramentas para simulação de ataques de engenharia social e treinamento de conscientização
        </p>
        <div className="mt-2 text-sm text-purple-300">
          ⚠️ Uso autorizado apenas para treinamentos de segurança e testes próprios
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Formulário de Campanha de Phishing */}
        <div className="bg-gray-900 p-6 rounded-lg">
          <h3 className="text-lg font-bold text-white mb-4">🎣 Campanha de Phishing</h3>
          <form onSubmit={createCampaign} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Nome da Campanha
              </label>
              <input
                type="text"
                value={campaignForm.name}
                onChange={(e) => setCampaignForm({...campaignForm, name: e.target.value})}
                className="w-full p-2 bg-gray-800 border border-gray-600 rounded text-white"
                placeholder="Teste de Phishing Q1 2024"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Template
              </label>
              <select
                value={campaignForm.template_id}
                onChange={(e) => setCampaignForm({...campaignForm, template_id: e.target.value})}
                className="w-full p-2 bg-gray-800 border border-gray-600 rounded text-white"
                required
              >
                <option value="">Selecione um template...</option>
                {socialEngData.templates.map(template => (
                  <option key={template.id} value={template.id}>
                    {template.name} - {template.template_type}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Emails de Destino (separados por vírgula)
              </label>
              <textarea
                value={campaignForm.target_emails}
                onChange={(e) => setCampaignForm({...campaignForm, target_emails: e.target.value})}
                className="w-full p-2 bg-gray-800 border border-gray-600 rounded text-white h-20"
                placeholder="user1@empresa.com, user2@empresa.com"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Nome do Remetente
                </label>
                <input
                  type="text"
                  value={campaignForm.sender_name}
                  onChange={(e) => setCampaignForm({...campaignForm, sender_name: e.target.value})}
                  className="w-full p-2 bg-gray-800 border border-gray-600 rounded text-white"
                  placeholder="IT Support"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Email do Remetente
                </label>
                <input
                  type="email"
                  value={campaignForm.sender_email}
                  onChange={(e) => setCampaignForm({...campaignForm, sender_email: e.target.value})}
                  className="w-full p-2 bg-gray-800 border border-gray-600 rounded text-white"
                  placeholder="noreply@empresa.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                URL da Landing Page
              </label>
              <input
                type="url"
                value={campaignForm.landing_page_url}
                onChange={(e) => setCampaignForm({...campaignForm, landing_page_url: e.target.value})}
                className="w-full p-2 bg-gray-800 border border-gray-600 rounded text-white"
                placeholder="https://fake-login.example.com"
              />
            </div>

            <button
              type="submit"
              disabled={loading.campaign}
              className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white py-2 px-4 rounded font-medium"
            >
              {loading.campaign ? 'Criando Campanha...' : 'Criar Campanha'}
            </button>
          </form>
        </div>

        {/* Formulário de Treinamento de Conscientização */}
        <div className="bg-gray-900 p-6 rounded-lg">
          <h3 className="text-lg font-bold text-white mb-4">🎓 Treinamento de Conscientização</h3>
          <form onSubmit={createAwarenessTraining} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Título do Treinamento
              </label>
              <input
                type="text"
                value={awarenessForm.title}
                onChange={(e) => setAwarenessForm({...awarenessForm, title: e.target.value})}
                className="w-full p-2 bg-gray-800 border border-gray-600 rounded text-white"
                placeholder="Identificando Emails de Phishing"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Descrição
              </label>
              <textarea
                value={awarenessForm.description}
                onChange={(e) => setAwarenessForm({...awarenessForm, description: e.target.value})}
                className="w-full p-2 bg-gray-800 border border-gray-600 rounded text-white h-24"
                placeholder="Treinamento sobre como identificar e relatar tentativas de phishing..."
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Grupo Alvo
              </label>
              <select
                value={awarenessForm.target_group}
                onChange={(e) => setAwarenessForm({...awarenessForm, target_group: e.target.value})}
                className="w-full p-2 bg-gray-800 border border-gray-600 rounded text-white"
              >
                <option value="all">Todos os funcionários</option>
                <option value="it">Equipe de TI</option>
                <option value="management">Gestores</option>
                <option value="finance">Financeiro</option>
                <option value="hr">Recursos Humanos</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Nível de Dificuldade
              </label>
              <select
                value={awarenessForm.difficulty_level}
                onChange={(e) => setAwarenessForm({...awarenessForm, difficulty_level: e.target.value})}
                className="w-full p-2 bg-gray-800 border border-gray-600 rounded text-white"
              >
                <option value="easy">Fácil</option>
                <option value="medium">Médio</option>
                <option value="hard">Difícil</option>
                <option value="expert">Expert</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={loading.awareness}
              className="w-full bg-pink-600 hover:bg-pink-700 disabled:bg-gray-600 text-white py-2 px-4 rounded font-medium"
            >
              {loading.awareness ? 'Criando Treinamento...' : 'Criar Treinamento'}
            </button>
          </form>
        </div>
      </div>

      {/* Status da Campanha Ativa */}
      {socialEngData.activeCampaign && (
        <div className="bg-gray-900 p-6 rounded-lg">
          <h3 className="text-lg font-bold text-white mb-4">📊 Campanha Ativa</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gray-800 p-4 rounded">
              <div className="text-sm text-gray-400">Nome</div>
              <div className="text-white font-medium">{socialEngData.activeCampaign.name}</div>
            </div>
            <div className="bg-gray-800 p-4 rounded">
              <div className="text-sm text-gray-400">Status</div>
              <div className={`font-medium ${
                socialEngData.activeCampaign.status === 'completed' ? 'text-green-400' :
                socialEngData.activeCampaign.status === 'failed' ? 'text-red-400' :
                'text-yellow-400'
              }`}>
                {socialEngData.activeCampaign.status}
              </div>
            </div>
            <div className="bg-gray-800 p-4 rounded">
              <div className="text-sm text-gray-400">Emails Enviados</div>
              <div className="text-white font-medium">
                {socialEngData.activeCampaign.emails_sent || 0}
              </div>
            </div>
            <div className="bg-gray-800 p-4 rounded">
              <div className="text-sm text-gray-400">Taxa de Cliques</div>
              <div className="text-white font-medium">
                {socialEngData.activeCampaign.click_rate || '0%'}
              </div>
            </div>
          </div>

          <div className="mt-4">
            <button
              onClick={() => getCampaignAnalytics(socialEngData.activeCampaign.campaign_id)}
              className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded"
            >
              Ver Analytics Completo
            </button>
          </div>
        </div>
      )}

      {/* Templates Disponíveis */}
      <div className="bg-gray-900 p-6 rounded-lg">
        <h3 className="text-lg font-bold text-white mb-4">📧 Templates Disponíveis</h3>
        {loading.templates ? (
          <div className="text-gray-400">Carregando templates...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {socialEngData.templates.map(template => (
              <div key={template.id} className="bg-gray-800 p-4 rounded">
                <div className="text-white font-medium">{template.name}</div>
                <div className="text-gray-400 text-sm mt-1">{template.subject}</div>
                <div className={`text-xs mt-2 px-2 py-1 rounded inline-block ${
                  template.template_type === 'phishing' ? 'bg-red-900 text-red-300' :
                  template.template_type === 'awareness' ? 'bg-blue-900 text-blue-300' :
                  'bg-gray-700 text-gray-300'
                }`}>
                  {template.template_type}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SocialEngineering;