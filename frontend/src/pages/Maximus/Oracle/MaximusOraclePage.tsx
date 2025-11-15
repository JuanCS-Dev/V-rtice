import { Card, CardHeader, CardTitle } from "@/components/ui";
import { TrendingUp, Activity, Brain, Zap, AlertTriangle } from "lucide-react";

export default function MaximusOraclePage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3.5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[rgb(var(--text-primary))] leading-none">
            Oracle Predictions
          </h1>
          <p className="text-[11px] text-[rgb(var(--text-tertiary))] mt-2 font-medium tracking-wide leading-none">
            ML-Powered Predictive Analytics & Threat Forecasting
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
              Predictions Today
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="text-3xl font-bold tabular-nums leading-none">
              24
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Avg Confidence
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="text-3xl font-bold tabular-nums leading-none">
              89
              <span className="text-sm text-[rgb(var(--text-tertiary))]">
                %
              </span>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Threats Predicted
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="text-3xl font-bold tabular-nums leading-none">
              7
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Anomalies Detected
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="text-3xl font-bold tabular-nums leading-none">
              12
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle
                className="h-5 w-5 text-red-600"
                strokeWidth={2.5}
              />
              <CardTitle>Threat Predictions</CardTitle>
            </div>
            <div className="mt-3 space-y-2 text-sm text-[rgb(var(--text-secondary))]">
              <div className="flex justify-between">
                <span>DDoS Attack</span>
                <span className="font-semibold">92% prob.</span>
              </div>
              <div className="flex justify-between">
                <span>Phishing Campaign</span>
                <span className="font-semibold">87% prob.</span>
              </div>
              <div className="flex justify-between">
                <span>Data Exfiltration</span>
                <span className="font-semibold">76% prob.</span>
              </div>
            </div>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-amber-600" strokeWidth={2.5} />
              <CardTitle>Anomaly Detection</CardTitle>
            </div>
            <div className="mt-3 space-y-2 text-sm text-[rgb(var(--text-secondary))]">
              <div className="flex justify-between">
                <span>Network Traffic</span>
                <span className="font-semibold">High</span>
              </div>
              <div className="flex justify-between">
                <span>User Behavior</span>
                <span className="font-semibold">Medium</span>
              </div>
              <div className="flex justify-between">
                <span>Resource Usage</span>
                <span className="font-semibold">Low</span>
              </div>
            </div>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-purple-600" strokeWidth={2.5} />
              <CardTitle>ML Models Active</CardTitle>
            </div>
            <div className="mt-3 space-y-2 text-sm text-[rgb(var(--text-secondary))]">
              <div>• Threat Classification</div>
              <div>• Behavior Analysis</div>
              <div>• Pattern Recognition</div>
              <div>• Time Series Forecasting</div>
            </div>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <TrendingUp
              className="h-5 w-5 text-primary-600"
              strokeWidth={2.5}
            />
            <CardTitle>Predictive Analytics Engine</CardTitle>
          </div>
          <div className="mt-2 text-sm text-[rgb(var(--text-secondary))]">
            O Oracle utiliza machine learning e predictive coding para antecipar
            ameaças, anomalias e incidentes de segurança. Análise de séries
            temporais, reconhecimento de padrões comportamentais e modelos
            preditivos treinados com dados históricos fornecem insights
            acionáveis com alta confiança (média de 89%).
          </div>
        </CardHeader>
      </Card>
    </div>
  );
}
