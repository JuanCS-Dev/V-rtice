// src/components/DossierPanel.jsx

import React from 'react';
import './DossierPanel.css';

// Função auxiliar para aplicar classes de status baseadas nos dados
const getStatusClass = (status) => {
  switch (status?.toLowerCase()) {
    case 'foragido':
    case 'roubado':
      return 'status-critical'; // Vermelho
    case 'em observação':
    case 'suspeito':
      return 'status-warning'; // Laranja/Amarelo
    case 'preso':
      return 'status-info'; // Azul
    default:
      return ''; // Verde/Padrão
  }
};

const DossierPanel = ({ suspect }) => {
  if (!suspect) {
    return <div className="dossier-panel">Nenhum alvo selecionado.</div>;
  }

  return (
    <div className="dossier-panel">
      
      {/* --- SEÇÃO DE IDENTIFICAÇÃO --- */}
      <div className="section">
        <div className="section-title">IDENTIFICAÇÃO</div>
        <div className="id-section">
          {suspect.photoUrl && <img src={suspect.photoUrl} alt={suspect.name} className="suspect-photo" />}
          <div className="id-details">
            <h2>{suspect.name}</h2>
            <p>CPF: {suspect.cpf}</p>
            <p>Status: <span className={`status-badge ${getStatusClass(suspect.status)}`}>{suspect.status}</span></p>
          </div>
        </div>
      </div>

      {/* --- SEÇÃO DE ATIVOS --- */}
      <div className="section">
        <div className="section-title">ATIVOS ASSOCIADOS</div>
        {suspect.assets.vehicles.map(vehicle => (
          <div key={vehicle.plate} className="asset-item">
            <span className="asset-icon">🚗</span>
            <span className={`asset-plate ${getStatusClass(vehicle.status)}`}>{vehicle.plate}</span>
            <span className="asset-details">{vehicle.model} - {vehicle.color}</span>
          </div>
        ))}
      </div>

      {/* --- SEÇÃO DE ASSOCIADOS --- */}
      <div className="section">
        <div className="section-title">ASSOCIADOS CONHECIDOS</div>
        {suspect.associates.map(assoc => (
          <div key={assoc.name} className="associate-item">
            <span className="associate-icon">👤</span>
            <span className="associate-name">{assoc.name}</span>
            <span className={`associate-status ${getStatusClass(assoc.status)}`}>({assoc.status})</span>
          </div>
        ))}
      </div>

    </div>
  );
};

export default DossierPanel;
