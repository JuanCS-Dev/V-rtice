import { Card, CardHeader, CardTitle } from "@/components/ui";
import { Database, Activity } from "lucide-react";

export default function MaximusMemoryPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3.5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[rgb(var(--text-primary))] leading-none">
            Memory Systems
          </h1>
          <p className="text-[11px] text-[rgb(var(--text-tertiary))] mt-2 font-medium tracking-wide leading-none">
            Working, Episodic & Semantic Memory Architecture
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-[rgb(var(--border))] bg-[rgb(var(--card))] px-2.5 py-1.5 shadow-sm self-start">
          <Activity
            className="h-3.5 w-3.5 text-primary-500"
            strokeWidth={2.5}
          />
          <span className="text-[11px] font-semibold text-[rgb(var(--text-secondary))] leading-none">
            Active
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Working Memory</CardTitle>
            <div className="mt-3 space-y-2 text-sm text-[rgb(var(--text-secondary))]">
              <div className="flex justify-between">
                <span>Current Context</span>
                <span className="font-semibold">Active</span>
              </div>
              <div className="flex justify-between">
                <span>Session Duration</span>
                <span className="font-semibold">12m</span>
              </div>
              <div className="flex justify-between">
                <span>Cache</span>
                <span className="font-semibold">Redis</span>
              </div>
            </div>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Episodic Memory</CardTitle>
            <div className="mt-3 space-y-2 text-sm text-[rgb(var(--text-secondary))]">
              <div className="flex justify-between">
                <span>Conversations</span>
                <span className="font-semibold">25</span>
              </div>
              <div className="flex justify-between">
                <span>Total Entries</span>
                <span className="font-semibold">847</span>
              </div>
              <div className="flex justify-between">
                <span>Storage</span>
                <span className="font-semibold">ChromaDB</span>
              </div>
            </div>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Semantic Memory</CardTitle>
            <div className="mt-3 space-y-2 text-sm text-[rgb(var(--text-secondary))]">
              <div className="flex justify-between">
                <span>Knowledge Entries</span>
                <span className="font-semibold">1.2K</span>
              </div>
              <div className="flex justify-between">
                <span>RAG System</span>
                <span className="font-semibold">Active</span>
              </div>
              <div className="flex justify-between">
                <span>Graph DB</span>
                <span className="font-semibold">Neo4j</span>
              </div>
            </div>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5 text-primary-600" strokeWidth={2.5} />
            <CardTitle>Multi-layered Memory Architecture</CardTitle>
          </div>
          <div className="mt-2 text-sm text-[rgb(var(--text-secondary))]">
            Sistema de memória inspirado na neurociência: Working Memory
            (contexto imediato via Redis), Episodic Memory (25 conversações via
            ChromaDB), Semantic Memory (1.2K entradas de conhecimento via Neo4j
            + RAG). Integração completa para contextualização e aprendizado
            contínuo.
          </div>
        </CardHeader>
      </Card>
    </div>
  );
}
