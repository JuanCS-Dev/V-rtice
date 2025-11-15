import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui";
import { Activity } from "lucide-react";
import { ThreatDetectionForm } from "@/features/immunis/components/ThreatDetectionForm";

export default function ImmunisPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[rgb(var(--text-primary))]">
          Immunis System
        </h1>
        <p className="mt-1 text-sm text-[rgb(var(--text-secondary))]">
          Adaptive immune system for autonomous threat detection and response
        </p>
      </div>

      {/* Threat Detection Form */}
      <ThreatDetectionForm />

      {/* Info Card */}
      <Card variant="elevated">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary-600" />
            <CardTitle>Biological Immune System Metaphor</CardTitle>
          </div>
          <CardDescription className="mt-2">
            Immunis uses a biological immune system approach with specialized
            agents (B-cells, T-cells, dendritic cells) to detect, contain, and
            eliminate threats autonomously while maintaining system homeostasis.
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}
