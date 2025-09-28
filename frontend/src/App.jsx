// /home/juan/vertice-dev/frontend/src/App.jsx

import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import { consultarPlacaApi } from './api/sinesp';
import Header from './components/Header';
import SidePanel from './components/SidePanel';
import DossierPanel from './components/DossierPanel';
import MapPanel from './components/MapPanel';
import Footer from './components/Footer';
import ModalOcorrencias from './components/ModalOcorrencias';
import ModalRelatorio from './components/ModalRelatorio';
import AdminDashboard from './components/AdminDashboard';
import CyberDashboard from './components/CyberDashboard';
import OSINTDashboard from './components/OSINTDashboard'; // NOVO IMPORT

function App() {
  // Estados existentes
  const [placa, setPlaca] = useState('');
  const [dossierData, setDossierData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [alerts, setAlerts] = useState([]);
  const [searchHistory, setSearchHistory] = useState([]);
  const [ocorrenciasVisivel, setOcorrenciasVisivel] = useState(false);
  const [relatorioVisivel, setRelatorioVisivel] = useState(false);
  const [placasSuspeitas, setPlacasSuspeitas] = useState(new Set());
  
  // ESTADO ATUALIZADO: Agora inclui 'osint'
  const [currentView, setCurrentView] = useState('main'); // 'main', 'admin', 'cyber' ou 'osint'

  // Effects existentes
  useEffect(() => { 
    const timer = setInterval(() => setCurrentTime(new Date()), 1000); 
    return () => clearInterval(timer); 
  }, []);

  useEffect(() => { 
    const alertTimer = setInterval(() => { 
      if (Math.random() > 0.85) { 
        const alertTypes = [
          { type: 'INFO', message: 'Sistema de monitoramento ativo' },
          { type: 'WARNING', message: 'Atividade suspeita detectada' }
        ]; 
        const randomAlert = alertTypes[Math.floor(Math.random() * alertTypes.length)]; 
        const newAlert = { 
          id: Date.now(), 
          ...randomAlert, 
          timestamp: new Date().toLocaleTimeString() 
        }; 
        setAlerts(prev => [newAlert, ...prev.slice(0, 4)]); 
      }
    }, 8000); 
    return () => clearInterval(alertTimer); 
  }, []);

  // Funções existentes
  const handleMarcarSuspeito = (placaParaMarcar) => { 
    setPlacasSuspeitas(prevSet => { 
      const newSet = new Set(prevSet); 
      newSet.add(placaParaMarcar); 
      return newSet; 
    }); 
  };

  const handleSearch = async () => { 
    if (!placa.trim()) return; 
    setLoading(true); 
    setError(null); 
    setDossierData(null); 
    try { 
      const data = await consultarPlacaApi(placa); 
      if (data.error) { 
        throw new Error(data.error); 
      } 
      const dataWithLocation = { 
        ...data, 
        lastKnownLocation: data.lastKnownLocation || { lat: -16.328, lng: -48.953 } 
      }; 
      setDossierData(dataWithLocation); 
      setSearchHistory(prev => [placa.toUpperCase(), ...prev.filter(p => p !== placa.toUpperCase())].slice(0, 10)); 
    } catch (err) { 
      setError(err.message); 
    } finally { 
      setLoading(false); 
    }
  };

  const handleKeyPress = (e) => { 
    if (e.key === 'Enter') { 
      handleSearch(); 
    }
  };

  const handleVerOcorrencias = () => { 
    if (dossierData && dossierData.ocorrencias) { 
      setOcorrenciasVisivel(true); 
    }
  };

  const handleGerarRelatorio = () => { 
    if (dossierData) { 
      setRelatorioVisivel(true); 
    }
  };

  // RENDERIZAÇÃO CONDICIONAL ATUALIZADA: Inclui todas as dashboards
  if (currentView === 'admin') {
    return <AdminDashboard setCurrentView={setCurrentView} />;
  }

  if (currentView === 'cyber') {
    return <CyberDashboard setCurrentView={setCurrentView} />;
  }

  if (currentView === 'osint') {
    return <OSINTDashboard setCurrentView={setCurrentView} />;
  }

  // Dashboard principal (operações gerais)
  return (
    <div className="h-screen w-screen bg-gradient-to-br from-gray-900 via-black to-gray-800 text-green-400 font-mono overflow-hidden flex flex-col">
      <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-green-400 to-transparent animate-pulse z-20"></div>
      
      <Header
        currentTime={currentTime} 
        placa={placa} 
        setPlaca={setPlaca}
        loading={loading} 
        handleSearch={handleSearch} 
        handleKeyPress={handleKeyPress}
        searchHistory={searchHistory}
        setCurrentView={setCurrentView}
        currentView={currentView}
      />

      <main className="flex-1 flex min-h-0">
        <SidePanel alerts={alerts} />
        <div className="flex-1 flex min-w-0">
          <DossierPanel 
            loading={loading} 
            error={error} 
            dossierData={dossierData} 
            onVerOcorrencias={handleVerOcorrencias}
            onMarcarSuspeito={handleMarcarSuspeito}
            placasSuspeitas={placasSuspeitas}
            onGerarRelatorio={handleGerarRelatorio}
          />
          <MapPanel dossierData={dossierData} />
        </div>
      </main>

      <Footer searchHistory={searchHistory} />

      {ocorrenciasVisivel && dossierData && ReactDOM.createPortal( 
        <ModalOcorrencias 
          ocorrencias={dossierData.ocorrencias} 
          onClose={() => setOcorrenciasVisivel(false)} 
        />, 
        document.getElementById('modal-root')
      )}
      
      {relatorioVisivel && dossierData && ReactDOM.createPortal( 
        <ModalRelatorio 
          dossierData={dossierData} 
          onClose={() => setRelatorioVisivel(false)} 
        />, 
        document.getElementById('modal-root')
      )}
    </div>
  );
}

export default App;
