import { Card, CardHeader, CardTitle } from "@/components/ui";
import { MessageSquare, Activity } from "lucide-react";
import { AIChatInterface } from "@/features/maximus/components/AIChatInterface";

export default function MaximusChatPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3.5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[rgb(var(--text-primary))] leading-none">
            AI Chat Interface
          </h1>
          <p className="text-[11px] text-[rgb(var(--text-tertiary))] mt-2 font-medium tracking-wide leading-none">
            Converse com Maximus AI - 57 ferramentas disponíveis
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-[rgb(var(--border))] bg-[rgb(var(--card))] px-2.5 py-1.5 shadow-sm self-start">
          <Activity
            className="h-3.5 w-3.5 text-primary-500"
            strokeWidth={2.5}
          />
          <span className="text-[11px] font-semibold text-[rgb(var(--text-secondary))] leading-none">
            Online
          </span>
        </div>
      </div>

      {/* Chat Interface */}
      <AIChatInterface />

      {/* Info Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <MessageSquare
              className="h-5 w-5 text-primary-600"
              strokeWidth={2.5}
            />
            <CardTitle>Cognitive Capabilities</CardTitle>
          </div>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <div className="font-semibold text-[rgb(var(--text-primary))]">
                Reasoning
              </div>
              <p className="text-[rgb(var(--text-secondary))] mt-1">
                Chain of Thought, Confidence Scoring, Self-Reflection
              </p>
            </div>
            <div>
              <div className="font-semibold text-[rgb(var(--text-primary))]">
                Memory
              </div>
              <p className="text-[rgb(var(--text-secondary))] mt-1">
                Working, Episodic (25 conversations), Semantic (Vector DB)
              </p>
            </div>
            <div>
              <div className="font-semibold text-[rgb(var(--text-primary))]">
                Tools
              </div>
              <p className="text-[rgb(var(--text-secondary))] mt-1">
                57 ferramentas: Basic (15), Advanced (22), Offensive (12)
              </p>
            </div>
          </div>
        </CardHeader>
      </Card>
    </div>
  );
}
