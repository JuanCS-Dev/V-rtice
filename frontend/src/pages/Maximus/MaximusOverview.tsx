import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui";
import {
  Brain,
  Activity,
  MessageSquare,
  Wrench,
  TrendingUp,
  Shield,
  Zap,
  BarChart3,
  Database,
  Settings,
} from "lucide-react";
import { Link } from "react-router-dom";

export default function MaximusOverview() {
  const modules = [
    {
      name: "AI Chat",
      description: "Conversa com o assistente Maximus AI",
      href: "/maximus/chat",
      icon: MessageSquare,
      color: "text-primary-600",
      stats: "57 ferramentas disponíveis",
    },
    {
      name: "Tools",
      description: "Arsenal de 57 ferramentas de segurança",
      href: "/maximus/tools",
      icon: Wrench,
      color: "text-blue-600",
      stats: "3 categorias",
    },
    {
      name: "Oracle",
      description: "Predições e análises preditivas",
      href: "/maximus/oracle",
      icon: TrendingUp,
      color: "text-purple-600",
      stats: "ML-powered",
    },
    {
      name: "Sentinel",
      description: "Monitoramento em tempo real",
      href: "/maximus/sentinel",
      icon: Shield,
      color: "text-red-600",
      stats: "Real-time",
    },
    {
      name: "Intelligence",
      description: "Threat Intelligence e análises",
      href: "/maximus/intelligence",
      icon: Zap,
      color: "text-amber-600",
      stats: "Multi-source",
    },
    {
      name: "Analytics",
      description: "Métricas e análises do sistema",
      href: "/maximus/analytics",
      icon: BarChart3,
      color: "text-cyan-600",
      stats: "Dashboard",
    },
    {
      name: "Memory",
      description: "Sistemas de memória (Working, Episodic, Semantic)",
      href: "/maximus/memory",
      icon: Database,
      color: "text-indigo-600",
      stats: "3 sistemas",
    },
    {
      name: "Settings",
      description: "Configurações do Maximus",
      href: "/maximus/settings",
      icon: Settings,
      color: "text-gray-600",
      stats: "Configuração",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3.5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[rgb(var(--text-primary))] leading-none">
            MAXIMUS AI Ecosystem
          </h1>
          <p className="text-[11px] text-[rgb(var(--text-tertiary))] mt-2 font-medium tracking-wide leading-none">
            Neuro-Inspired AI System for Security Analysis & Decision Support
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-[rgb(var(--border))] bg-[rgb(var(--card))] px-2.5 py-1.5 shadow-sm self-start">
          <Activity
            className="h-3.5 w-3.5 text-primary-500"
            strokeWidth={2.5}
          />
          <span className="text-[11px] font-semibold text-[rgb(var(--text-secondary))] leading-none">
            System Active
          </span>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3.5">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Tools Available
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="text-3xl font-bold tabular-nums leading-none">
              57
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Active Sessions
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
              Memory Entries
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-5">
            <div className="text-3xl font-bold tabular-nums leading-none">
              1.2K
            </div>
          </div>
        </Card>
      </div>

      {/* Modules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
        {modules.map((module) => (
          <Link key={module.href} to={module.href} className="group">
            <Card className="h-full transition-all duration-200 hover:-translate-y-px hover:shadow-md cursor-pointer">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <module.icon
                    className={`h-8 w-8 ${module.color}`}
                    strokeWidth={2}
                  />
                  <span className="text-[10px] font-medium text-[rgb(var(--text-tertiary))] uppercase tracking-wider leading-none">
                    {module.stats}
                  </span>
                </div>
                <CardTitle className="mt-4 text-base group-hover:text-primary-600 transition-colors">
                  {module.name}
                </CardTitle>
                <CardDescription className="mt-2 text-sm">
                  {module.description}
                </CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-primary-600" strokeWidth={2.5} />
            <CardTitle>About Maximus AI</CardTitle>
          </div>
          <CardDescription className="mt-2">
            Maximus is a neuro-inspired AI system designed for advanced security
            analysis and decision support. It features 57 specialized tools
            across 3 categories (Basic, Advanced, Offensive), multi-layered
            memory systems (Working, Episodic, Semantic), and predictive
            analytics powered by machine learning. The system integrates with
            44+ microservices and provides real-time threat intelligence and
            autonomous security operations.
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}
