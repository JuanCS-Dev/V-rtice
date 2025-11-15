import { Card, CardHeader, CardTitle } from "@/components/ui";
import { BarChart3, Activity } from "lucide-react";

export default function MaximusAnalyticsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3.5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[rgb(var(--text-primary))] leading-none">
            System Analytics
          </h1>
          <p className="text-[11px] text-[rgb(var(--text-tertiary))] mt-2 font-medium tracking-wide leading-none">
            Performance Metrics & System Insights
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-[rgb(var(--border))] bg-[rgb(var(--card))] px-2.5 py-1.5 shadow-sm self-start">
          <Activity
            className="h-3.5 w-3.5 text-primary-500"
            strokeWidth={2.5}
          />
          <span className="text-[11px] font-semibold text-[rgb(var(--text-secondary))] leading-none">
            Analyzing
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-3.5">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Avg Response Time
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="text-3xl font-bold tabular-nums leading-none">
              234
              <span className="text-sm text-[rgb(var(--text-tertiary))]">
                ms
              </span>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Tool Executions
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="text-3xl font-bold tabular-nums leading-none">
              1.2K
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Accuracy Rate
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="text-3xl font-bold tabular-nums leading-none">
              94
              <span className="text-sm text-[rgb(var(--text-tertiary))]">
                %
              </span>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Memory Usage
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="text-3xl font-bold tabular-nums leading-none">
              67
              <span className="text-sm text-[rgb(var(--text-tertiary))]">
                %
              </span>
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-primary-600" strokeWidth={2.5} />
            <CardTitle>Performance Analytics</CardTitle>
          </div>
          <div className="mt-2 text-sm text-[rgb(var(--text-secondary))]">
            Métricas de performance do sistema: tempo médio de resposta 234ms,
            1.2K execuções de ferramentas, taxa de acurácia 94%, uso de memória
            67%. Dashboard completo com métricas de reasoning, tool selection,
            memory efficiency e system health.
          </div>
        </CardHeader>
      </Card>
    </div>
  );
}
