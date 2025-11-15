import { Card, CardHeader, CardTitle } from "@/components/ui";
import { Zap, Activity } from "lucide-react";

export default function MaximusIntelligencePage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3.5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[rgb(var(--text-primary))] leading-none">
            Threat Intelligence
          </h1>
          <p className="text-[11px] text-[rgb(var(--text-tertiary))] mt-2 font-medium tracking-wide leading-none">
            Multi-source Threat Intelligence & Security Analytics
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-[rgb(var(--border))] bg-[rgb(var(--card))] px-2.5 py-1.5 shadow-sm self-start">
          <Activity
            className="h-3.5 w-3.5 text-primary-500"
            strokeWidth={2.5}
          />
          <span className="text-[11px] font-semibold text-[rgb(var(--text-secondary))] leading-none">
            Collecting
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-3.5">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Intel Sources
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="text-3xl font-bold tabular-nums leading-none">
              23
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              IOCs Today
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="text-3xl font-bold tabular-nums leading-none">
              347
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Active Campaigns
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="text-3xl font-bold tabular-nums leading-none">
              12
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Critical Threats
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="text-3xl font-bold tabular-nums leading-none">
              5
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-primary-600" strokeWidth={2.5} />
            <CardTitle>Threat Intelligence Platform</CardTitle>
          </div>
          <div className="mt-2 text-sm text-[rgb(var(--text-secondary))]">
            Agregação multi-fonte de inteligência de ameaças (23 fontes),
            correlação de IOCs (347 hoje), tracking de campanhas ativas (12) e
            análise de ameaças críticas (5). Integra com OSINT, SIEM e
            frameworks de threat intel para contexto enriquecido.
          </div>
        </CardHeader>
      </Card>
    </div>
  );
}
