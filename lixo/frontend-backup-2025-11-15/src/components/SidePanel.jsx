import React from "react";

const SidePanel = ({ alerts }) => {
  return (
    <aside className="w-80 border-r border-green-400/30 bg-black/30 backdrop-blur-sm overflow-y-auto">
      <div className="p-4 border-b border-green-400/30">
        <h3 className="text-green-400 font-bold mb-3 tracking-wide">
          STATUS DO SISTEMA
        </h3>
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-green-400/70">OPERACIONAL</span>
            <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-green-400/70">APIs ATIVAS</span>
            <span className="text-green-400">2/2</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-green-400/70">LATÊNCIA</span>
            <span className="text-green-400">127ms</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-green-400/70">UPTIME</span>
            <span className="text-green-400">99.8%</span>
          </div>
        </div>
      </div>

      <div className="p-4">
        <h3 className="text-green-400 font-bold mb-3 tracking-wide">
          ALERTAS EM TEMPO REAL
        </h3>
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {alerts.length === 0 ? (
            <div className="text-green-400/50 text-xs text-center py-4">
              Sistema em monitoramento...
            </div>
          ) : (
            alerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-3 rounded border-l-4 ${
                  alert.type === "WARNING"
                    ? "border-yellow-400 bg-yellow-400/10 text-yellow-400"
                    : "border-green-400 bg-green-400/10 text-green-400"
                }`}
              >
                <div className="flex justify-between items-start">
                  <span className="text-xs font-semibold">{alert.type}</span>
                  <span className="text-xs opacity-70">{alert.timestamp}</span>
                </div>
                <p className="text-xs mt-1">{alert.message}</p>
              </div>
            ))
          )}
        </div>
      </div>
    </aside>
  );
};

export default SidePanel;
