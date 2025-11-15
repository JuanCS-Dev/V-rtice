import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui";
import { Users, Activity, CheckCircle2, Clock } from "lucide-react";

export default function HITLPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3.5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[rgb(var(--text-primary))] leading-none">
            HCL/HITL Workflow
          </h1>
          <p className="text-[11px] text-[rgb(var(--text-tertiary))] mt-2 font-medium tracking-wide leading-none">
            Human-in-the-Loop Decision Workflow
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-[rgb(var(--border))] bg-[rgb(var(--card))] px-2.5 py-1.5 shadow-sm self-start">
          <Activity
            className="h-3.5 w-3.5 text-primary-500"
            strokeWidth={2.5}
          />
          <span className="text-[11px] font-semibold text-[rgb(var(--text-secondary))] leading-none">
            Workflow Active
          </span>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3.5">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Pending Decisions
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="flex items-center gap-3">
              <Clock className="h-8 w-8 text-amber-500" strokeWidth={2} />
              <div className="text-3xl font-bold tabular-nums leading-none">
                7
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Approved Today
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="flex items-center gap-3">
              <CheckCircle2
                className="h-8 w-8 text-primary-500"
                strokeWidth={2}
              />
              <div className="text-3xl font-bold tabular-nums leading-none">
                24
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              In Analysis
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
              Auto-Executed
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="text-3xl font-bold tabular-nums leading-none">
              156
            </div>
          </div>
        </Card>
      </div>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5 text-primary-600" strokeWidth={2.5} />
            <CardTitle>Human-in-the-Loop Workflow</CardTitle>
          </div>
          <CardDescription className="mt-2">
            The HCL/HITL system provides a complete workflow for human oversight
            of automated security decisions. Tasks flow through Analysis →
            Planning → Execution phases, with critical decisions requiring human
            approval before execution. The Knowledge Base learns from past
            decisions to improve automated decision-making over time.
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}
