import { Card, CardHeader, CardTitle } from "@/components/ui";
import { Shield, Activity } from "lucide-react";

export default function MaximusSentinelPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3.5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[rgb(var(--text-primary))] leading-none">
            Sentinel Real-time Monitoring
          </h1>
          <p className="text-[11px] text-[rgb(var(--text-tertiary))] mt-2 font-medium tracking-wide leading-none">
            Continuous Security Monitoring & Real-time Threat Detection
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-[rgb(var(--border))] bg-[rgb(var(--card))] px-2.5 py-1.5 shadow-sm self-start">
          <Activity
            className="h-3.5 w-3.5 text-primary-500"
            strokeWidth={2.5}
          />
          <span className="text-[11px] font-semibold text-[rgb(var(--text-secondary))] leading-none">
            Monitoring Active
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-3.5">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Events/sec
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="text-3xl font-bold tabular-nums leading-none">
              847
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Active Alerts
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="text-3xl font-bold tabular-nums leading-none">
              3
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Threats Blocked
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="text-3xl font-bold tabular-nums leading-none">
              156
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Response Time
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="text-3xl font-bold tabular-nums leading-none">
              23
              <span className="text-sm text-[rgb(var(--text-tertiary))]">
                ms
              </span>
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary-600" strokeWidth={2.5} />
            <CardTitle>Real-time Security Sentinel</CardTitle>
          </div>
          <div className="mt-2 text-sm text-[rgb(var(--text-secondary))]">
            Sentinel monitora continuamente 847 eventos por segundo, detectando
            e bloqueando ameaças em tempo real com latência média de 23ms.
            Integra com MAPE-K loop para resposta autônoma e homeostatic control
            para auto-regulação do sistema.
          </div>
        </CardHeader>
      </Card>
    </div>
  );
}
