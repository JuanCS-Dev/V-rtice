import React from 'react';
import { useFocusTrap } from '../hooks/useFocusTrap';

const ModalRelatorio = ({ dossierData, onClose }) => {
  const modalRef = useFocusTrap({
    active: true,
    autoFocus: true,
    returnFocus: true,
    onEscape: onClose,
    allowOutsideClick: false
  });

  const handlePrint = () => {
    // Esconde os botões para não aparecerem na impressão
    const printButton = document.getElementById('print-button');
    const closeButton = document.getElementById('close-button');
    printButton.style.display = 'none';
    closeButton.style.display = 'none';

    window.print(); // Abre a janela de impressão do navegador

    // Mostra os botões novamente após a impressão
    printButton.style.display = 'block';
    closeButton.style.display = 'block';
  };

  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in"
      role="presentation"
    >
      <div
        ref={modalRef}
        className="bg-gray-100 text-gray-800 font-sans w-full max-w-4xl h-[90vh] rounded-lg shadow-2xl flex flex-col animate-slide-up"
        onClick={e => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-report-title"
      >
        <header className="flex items-center justify-between p-4 bg-gray-200 border-b border-gray-300">
          <h2 id="modal-report-title" className="text-xl font-bold text-gray-700">Relatório de Inteligência Veicular</h2>
          <div className="flex items-center space-x-2">
            <button
              id="print-button"
              onClick={handlePrint}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm"
              aria-label="Imprimir ou salvar relatório como PDF"
            >
              Imprimir / Salvar PDF
            </button>
            <button
              id="close-button"
              onClick={onClose}
              className="text-gray-600 hover:text-black transition-colors text-2xl leading-none"
              aria-label="Fechar relatório"
            >
              &times;
            </button>
          </div>
        </header>

        <main className="flex-1 p-8 overflow-y-auto">
          <section className="mb-6">
            <h3 className="text-lg font-semibold border-b border-gray-300 pb-2 mb-4">Informações do Veículo</h3>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div><strong>Placa:</strong> <span className="font-mono text-base">{dossierData.placa}</span></div>
              <div><strong>Situação:</strong> <span className="font-semibold text-red-600">{dossierData.situacao}</span></div>
              <div><strong>Risco:</strong> <span className="font-semibold">{dossierData.riskLevel}</span></div>
              <div className="col-span-2"><strong>Veículo:</strong> {dossierData.marca} {dossierData.modelo}</div>
              <div><strong>Cor:</strong> {dossierData.cor}</div>
              <div><strong>Ano/Modelo:</strong> {dossierData.ano}/{dossierData.anoModelo}</div>
              <div className="col-span-2"><strong>Chassi:</strong> <span className="font-mono">{dossierData.chassi}</span></div>
              <div className="col-span-3"><strong>Local:</strong> {dossierData.municipio} - {dossierData.uf}</div>
            </div>
          </section>

          <section>
            <h3 className="text-lg font-semibold border-b border-gray-300 pb-2 mb-4">Histórico de Ocorrências</h3>
            <div className="space-y-4 text-sm">
              {dossierData.ocorrencias.map(ocorrencia => (
                <div key={ocorrencia.id} className="border border-gray-200 rounded p-3">
                  <div className="flex justify-between font-semibold mb-1">
                    <span>{ocorrencia.tipo} (ID: {ocorrencia.id})</span>
                    <span>Status: {ocorrencia.status}</span>
                  </div>
                  <p className="text-gray-600 mb-2">{ocorrencia.resumo}</p>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Data: {new Date(ocorrencia.data).toLocaleDateString('pt-BR')}</span>
                    <span>Local: {ocorrencia.local}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </main>
      </div>
    </div>
  );
};

export default ModalRelatorio;
