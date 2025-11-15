import { Card, CardHeader, CardTitle } from "@/components/ui";
import { Settings, Activity } from "lucide-react";

export default function MaximusSettingsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3.5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[rgb(var(--text-primary))] leading-none">
            System Settings
          </h1>
          <p className="text-[11px] text-[rgb(var(--text-tertiary))] mt-2 font-medium tracking-wide leading-none">
            Configuration & Preferences
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-[rgb(var(--border))] bg-[rgb(var(--card))] px-2.5 py-1.5 shadow-sm self-start">
          <Activity
            className="h-3.5 w-3.5 text-primary-500"
            strokeWidth={2.5}
          />
          <span className="text-[11px] font-semibold text-[rgb(var(--text-secondary))] leading-none">
            Configured
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        <Card>
          <CardHeader>
            <CardTitle>Reasoning Engine</CardTitle>
            <div className="mt-3 space-y-2 text-sm text-[rgb(var(--text-secondary))]">
              <div className="flex justify-between">
                <span>Chain of Thought</span>
                <span className="font-semibold text-primary-600">Enabled</span>
              </div>
              <div className="flex justify-between">
                <span>Self-Reflection</span>
                <span className="font-semibold text-primary-600">Enabled</span>
              </div>
              <div className="flex justify-between">
                <span>Confidence Threshold</span>
                <span className="font-semibold">0.85</span>
              </div>
            </div>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Tool Execution</CardTitle>
            <div className="mt-3 space-y-2 text-sm text-[rgb(var(--text-secondary))]">
              <div className="flex justify-between">
                <span>Max Parallel Tools</span>
                <span className="font-semibold">5</span>
              </div>
              <div className="flex justify-between">
                <span>Timeout</span>
                <span className="font-semibold">30s</span>
              </div>
              <div className="flex justify-between">
                <span>Retry Strategy</span>
                <span className="font-semibold">Exponential</span>
              </div>
            </div>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Memory Configuration</CardTitle>
            <div className="mt-3 space-y-2 text-sm text-[rgb(var(--text-secondary))]">
              <div className="flex justify-between">
                <span>Episodic Limit</span>
                <span className="font-semibold">25 conversations</span>
              </div>
              <div className="flex justify-between">
                <span>Vector Dimensions</span>
                <span className="font-semibold">1536</span>
              </div>
              <div className="flex justify-between">
                <span>RAG Top-K</span>
                <span className="font-semibold">5</span>
              </div>
            </div>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Autonomic Core (MAPE-K)</CardTitle>
            <div className="mt-3 space-y-2 text-sm text-[rgb(var(--text-secondary))]">
              <div className="flex justify-between">
                <span>Homeostatic Control</span>
                <span className="font-semibold text-primary-600">Active</span>
              </div>
              <div className="flex justify-between">
                <span>Monitor Interval</span>
                <span className="font-semibold">5s</span>
              </div>
              <div className="flex justify-between">
                <span>Auto-scaling</span>
                <span className="font-semibold text-primary-600">Enabled</span>
              </div>
            </div>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Settings className="h-5 w-5 text-primary-600" strokeWidth={2.5} />
            <CardTitle>System Configuration</CardTitle>
          </div>
          <div className="mt-2 text-sm text-[rgb(var(--text-secondary))]">
            Configurações centralizadas do Maximus AI: Reasoning Engine (CoT,
            Self-Reflection), Tool Execution (5 parallel, 30s timeout), Memory
            (25 conversações, 1536 dims, RAG Top-5), Autonomic Core MAPE-K
            (homeostatic control, auto-scaling, monitor 5s).
          </div>
        </CardHeader>
      </Card>
    </div>
  );
}
