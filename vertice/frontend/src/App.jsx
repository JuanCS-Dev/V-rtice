// frontend/src/App.jsx

import React from 'react';
import './App.css';
import DossierPanel from './components/DossierPanel';
import MapComponent from './components/Map';

// --- ATUALIZAMOS NOSSOS DADOS DE TESTE ---
const mockSuspect = {
  name: 'Marcos "O Fantasma" Oliveira',
  cpf: '123.456.789-00',
  status: 'Foragido',
  photoUrl: 'https://i.pravatar.cc/150?u=a042581f4e29026704d',
  // ADICIONAMOS A LOCALIZAÇÃO
  lastKnownLocation: {
    lat: -16.328,
    lng: -48.953,
  },
  assets: {
    vehicles: [
      { plate: 'ABC-1234', model: 'Honda Civic', color: 'Preto', status: 'Regular' },
      { plate: 'XYZ-9876', model: 'Fiat Strada', color: 'Vermelho', status: 'Roubado' }
    ]
  },
  associates: [
    { name: 'Juliana "A Dama" Costa', status: 'Em Observação' },
    { name: 'Ricardo "O Ferramenta" Alves', status: 'Preso' }
  ]
};
// ------------------------------------------

function App() {
  const styles = {
    app: {
      backgroundColor: '#1a1a1a',
      color: '#00f0ff',
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      fontFamily: 'monospace',
    },
    header: {
      borderBottom: '1px solid #ff00ff',
      padding: '10px',
      textAlign: 'center',
    },
    main: {
      display: 'flex',
      flex: 1,
      overflow: 'hidden',
    },
    sidePanel: {
      width: '30%',
      minWidth: '350px',
    },
    mapArea: {
      flex: 1,
      borderLeft: '1px solid #555'
    },
    footer: {
      borderTop: '1px solid #ff00ff',
      padding: '10px',
      textAlign: 'center',
    }
  };

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        [ Barra de Comando Universal ]
      </header>
      <main style={styles.main}>
        <aside style={styles.sidePanel}>
          <DossierPanel suspect={mockSuspect} />
        </aside>
        <section style={styles.mapArea}>
          {/* AGORA PASSAMOS A LOCALIZAÇÃO PARA O MAPA */}
          <MapComponent location={[mockSuspect.lastKnownLocation.lat, mockSuspect.lastKnownLocation.lng]} />
        </section>
      </main>
      <footer style={styles.footer}>
        [ Linha do Tempo ]
      </footer>
    </div>
  );
}

export default App;
