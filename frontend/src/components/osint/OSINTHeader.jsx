import React from 'react';
import { useTranslation } from 'react-i18next';
import { Breadcrumb } from '../shared/Breadcrumb';
import useKeyboardNavigation from '../../hooks/useKeyboardNavigation';

const OSINTHeader = ({ currentTime, setCurrentView, activeModule, setActiveModule }) => {
  const { t } = useTranslation();

  const modules = [
    { id: 'overview', name: t('dashboard.osint.modules.overview'), icon: '🛡️' },
    { id: 'aurora', name: t('dashboard.osint.modules.aurora'), icon: '🧠', isAI: true },
    { id: 'socialmedia', name: t('dashboard.osint.modules.socialmedia'), icon: '🔎', isWorldClass: true },
    { id: 'breachdata', name: t('dashboard.osint.modules.breachdata'), icon: '💾', isWorldClass: true },
    { id: 'username', name: t('dashboard.osint.modules.username'), icon: '👤' },
    { id: 'email', name: t('dashboard.osint.modules.email'), icon: '📧' },
    { id: 'phone', name: t('dashboard.osint.modules.phone'), icon: '📱' },
    { id: 'social', name: t('dashboard.osint.modules.social'), icon: '🌐' },
    { id: 'google', name: t('dashboard.osint.modules.google'), icon: '🌎' },
    { id: 'darkweb', name: t('dashboard.osint.modules.darkweb'), icon: '🌑' },
    { id: 'reports', name: t('dashboard.osint.modules.reports'), icon: '📊' }
  ];

  const { getItemProps } = useKeyboardNavigation({
    itemCount: modules.length,
    onSelect: (index) => setActiveModule(modules[index].id),
    orientation: 'horizontal',
    loop: true
  });

  return (
    <header className="relative border-b border-purple-400/30 bg-black/50 backdrop-blur-sm">
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 border-2 border-purple-400 rounded-lg flex items-center justify-center bg-purple-400/10">
            <span className="text-purple-400 font-bold text-xl">🔍</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-purple-400 tracking-wider">
              {t('dashboard.osint.title')}
            </h1>
            <p className="text-purple-400/70 text-sm tracking-widest">{t('dashboard.osint.subtitle')}</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <button
            onClick={() => setCurrentView('main')}
            className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-500 hover:to-green-600 text-black font-bold px-4 py-2 rounded-lg transition-all duration-300 tracking-wider text-sm"
            aria-label={t('navigation.back_to_hub')}
          >
            ← {t('common.back').toUpperCase()}
          </button>

          <div className="text-right">
            <div className="text-purple-400 font-bold text-lg">
              {currentTime.toLocaleTimeString()}
            </div>
            <div className="text-purple-400/70 text-sm">
              {currentTime.toLocaleDateString('pt-BR')}
            </div>
          </div>
        </div>
      </div>

      {/* Breadcrumb Navigation */}
      <div className="px-4 py-2 bg-gradient-to-r from-black/50 to-purple-900/20 border-t border-purple-400/10">
        <Breadcrumb
          items={[
            { label: 'VÉRTICE', icon: '🏠', onClick: () => setCurrentView('main') },
            { label: 'OSINT', icon: '🕵️' },
            { label: modules.find(m => m.id === activeModule)?.name.toUpperCase() || 'OVERVIEW', icon: modules.find(m => m.id === activeModule)?.icon }
          ]}
          className="text-purple-400"
        />
      </div>

      {/* Navigation Modules */}
      <nav 
        className="px-4 py-2 bg-black/30"
        role="navigation"
        aria-label="Módulos OSINT"
      >
        <div className="flex flex-wrap gap-2 justify-center items-center" role="tablist">
          {modules.map((module, index) => (
            <button
              key={module.id}
              {...getItemProps(index, {
                onClick: () => setActiveModule(module.id),
                role: 'tab',
                'aria-selected': activeModule === module.id,
                'aria-controls': `panel-${module.id}`,
                className: `px-3 py-1.5 rounded font-medium text-xs transition-all focus:outline-none focus:ring-2 focus:ring-purple-400/50 ${
                  activeModule === module.id
                    ? module.isAI
                      ? 'bg-gradient-to-r from-black via-green-900/40 to-green-700/60 text-gray-200 border border-green-700/30'
                      : module.isWorldClass
                        ? 'bg-gradient-to-r from-purple-900/40 to-pink-900/40 text-gray-200 border border-purple-400/50'
                        : 'bg-blue-950/30 text-blue-400 border border-blue-900/50'
                    : module.isAI
                      ? 'bg-gray-800/50 text-gray-400 border border-gray-700 hover:border-green-700/30'
                      : module.isWorldClass
                        ? 'bg-black/30 text-purple-400/70 border border-gray-700 hover:border-purple-400/50'
                        : 'bg-black/30 text-gray-400 border border-gray-700 hover:border-blue-900/30'
                }`
              })}
            >
              <span className="mr-1.5 text-[10px]" aria-hidden="true">{module.icon}</span>
              {module.name}
              {module.isWorldClass && <span className="ml-1.5 text-[10px]" aria-hidden="true">⭐</span>}
            </button>
          ))}
        </div>
      </nav>
    </header>
  );
};

export default OSINTHeader;