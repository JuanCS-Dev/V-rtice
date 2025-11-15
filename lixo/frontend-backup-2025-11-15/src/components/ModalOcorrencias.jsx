import React from "react";
import { useFocusTrap } from "../hooks/useFocusTrap";
import { formatDate } from "../utils/dateHelpers";

const ModalOcorrencias = ({ ocorrencias, onClose }) => {
  const modalRef = useFocusTrap({
    active: true,
    autoFocus: true,
    returnFocus: true,
    onEscape: onClose,
    allowOutsideClick: false,
  });

  return (
    // Overlay de fundo
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in"
      role="presentation"
    >
      {/* Container do Modal */}
      <div
        ref={modalRef}
        className="bg-gray-900 border border-green-400/50 w-full max-w-4xl h-[80vh] rounded-lg shadow-lg flex flex-col animate-slide-up"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-occurrences-title"
      >
        {/* Cabeçalho do Modal */}
        <header className="flex items-center justify-between p-4 border-b border-green-400/30 flex-shrink-0">
          <h2
            id="modal-occurrences-title"
            className="text-xl font-bold text-green-400 tracking-wider"
          >
            HISTÓRICO DE OCORRÊNCIAS
          </h2>
          <button
            onClick={onClose}
            className="text-green-400 hover:text-white transition-colors text-2xl leading-none"
            aria-label="Fechar histórico de ocorrências"
          >
            &times;
          </button>
        </header>

        {/* Corpo do Modal com scroll */}
        <main className="flex-1 p-6 overflow-y-auto">
          <div className="space-y-6">
            {ocorrencias.length > 0 ? (
              ocorrencias.map((ocorrencia) => (
                <div
                  key={ocorrencia.id}
                  className="border border-green-400/30 rounded-lg bg-black/30 p-4"
                >
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <span className="font-bold text-green-400">
                        {ocorrencia.tipo}
                      </span>
                      <span className="ml-4 text-green-400/60 text-sm font-mono">
                        ID: {ocorrencia.id}
                      </span>
                    </div>
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        ocorrencia.status === "Em Investigação"
                          ? "bg-yellow-500/20 text-yellow-400"
                          : "bg-gray-500/20 text-gray-400"
                      }`}
                    >
                      {ocorrencia.status}
                    </span>
                  </div>
                  <p className="text-green-400/80 mb-3">{ocorrencia.resumo}</p>
                  <div className="flex justify-between items-center text-xs text-green-400/60 border-t border-green-400/20 pt-2">
                    <span>
                      Data:{" "}
                      {formatDate(
                        ocorrencia.data,
                        { dateStyle: "short" },
                        "N/A",
                      )}
                    </span>
                    <span>Local: {ocorrencia.local}</span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-center text-green-400/70">
                Nenhuma ocorrência registrada para este veículo.
              </p>
            )}
          </div>
        </main>
      </div>
      {/* Animações simples via CSS embutido */}
      <style>{`
        @keyframes fade-in { from { opacity: 0; } to { opacity: 1; } }
        @keyframes slide-up { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        .animate-fade-in { animation: fade-in 0.3s ease-out forwards; }
        .animate-slide-up { animation: slide-up 0.4s ease-out forwards; }
      `}</style>
    </div>
  );
};

export default ModalOcorrencias;
