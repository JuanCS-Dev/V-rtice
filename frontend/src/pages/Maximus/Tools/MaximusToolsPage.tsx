import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui";
import { Wrench, Activity, Code, Cpu, Sword } from "lucide-react";

export default function MaximusToolsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3.5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[rgb(var(--text-primary))] leading-none">
            Tool Arsenal
          </h1>
          <p className="text-[11px] text-[rgb(var(--text-tertiary))] mt-2 font-medium tracking-wide leading-none">
            57 Specialized Security Tools
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-[rgb(var(--border))] bg-[rgb(var(--card))] px-2.5 py-1.5 shadow-sm self-start">
          <Activity
            className="h-3.5 w-3.5 text-primary-500"
            strokeWidth={2.5}
          />
          <span className="text-[11px] font-semibold text-[rgb(var(--text-secondary))] leading-none">
            57 Tools Active
          </span>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Basic Tools
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="flex items-center gap-3">
              <Code className="h-8 w-8 text-blue-500" strokeWidth={2} />
              <div className="text-3xl font-bold tabular-nums leading-none">
                15
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Advanced Tools
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="flex items-center gap-3">
              <Cpu className="h-8 w-8 text-purple-500" strokeWidth={2} />
              <div className="text-3xl font-bold tabular-nums leading-none">
                22
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Offensive Tools
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="flex items-center gap-3">
              <Sword className="h-8 w-8 text-red-500" strokeWidth={2} />
              <div className="text-3xl font-bold tabular-nums leading-none">
                12
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Tool Categories */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3.5">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Code className="h-5 w-5 text-blue-600" strokeWidth={2.5} />
              <CardTitle>Basic Tools (15)</CardTitle>
            </div>
            <CardDescription className="mt-2">
              <div className="space-y-1 text-sm">
                <div>• IP Intelligence</div>
                <div>• Threat Intelligence</div>
                <div>• Malware Analysis</div>
                <div>• Domain Analysis</div>
                <div>• SSL Monitoring</div>
                <div>• OSINT Operations</div>
                <div>• Network Scanning</div>
              </div>
            </CardDescription>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Cpu className="h-5 w-5 text-purple-600" strokeWidth={2.5} />
              <CardTitle>Advanced Tools (22)</CardTitle>
            </div>
            <CardDescription className="mt-2">
              <div className="space-y-1 text-sm">
                <div>• Behavioral Analytics</div>
                <div>• ML Models</div>
                <div>• Incident Response</div>
                <div>• Compliance Checking</div>
                <div>• SIEM Integration</div>
                <div>• DLP (Data Loss Prevention)</div>
                <div>• Forensics Analysis</div>
              </div>
            </CardDescription>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Sword className="h-5 w-5 text-red-600" strokeWidth={2.5} />
              <CardTitle>Offensive Tools (12)</CardTitle>
            </div>
            <CardDescription className="mt-2">
              <div className="space-y-1 text-sm">
                <div>• Network Reconnaissance</div>
                <div>• Vulnerability Scanning</div>
                <div>• Web Attack Simulation</div>
                <div>• BAS (Breach & Attack)</div>
                <div>• C2 Orchestration</div>
                <div>• Payload Generation</div>
                <div>• Exploitation Framework</div>
              </div>
            </CardDescription>
          </CardHeader>
        </Card>
      </div>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Wrench className="h-5 w-5 text-primary-600" strokeWidth={2.5} />
            <CardTitle>Tool System Architecture</CardTitle>
          </div>
          <CardDescription className="mt-2">
            O arsenal de 57 ferramentas do Maximus é organizado em 3 categorias
            principais. O Reasoning Engine seleciona e executa até 5 ferramentas
            em paralelo baseado no contexto e necessidade. Cada ferramenta
            retorna resultados estruturados que são sintetizados pelo sistema
            cognitivo para gerar respostas precisas e acionáveis.
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}
