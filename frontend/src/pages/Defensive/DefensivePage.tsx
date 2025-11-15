import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui";
import { Shield } from "lucide-react";
import { BehavioralAnalysisForm } from "@/features/defensive/components/BehavioralAnalysisForm";

export default function DefensivePage() {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[rgb(var(--text-primary))]">
          Defensive Security
        </h1>
        <p className="mt-1 text-sm text-[rgb(var(--text-secondary))]">
          Behavioral analysis, traffic monitoring, and threat detection
        </p>
      </div>

      {/* Behavioral Analysis Form */}
      <BehavioralAnalysisForm />

      {/* Info Card */}
      <Card variant="elevated">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary-600" />
            <CardTitle>Defensive Security</CardTitle>
          </div>
          <CardDescription className="mt-2">
            Analyze user and system behavior patterns to detect anomalies and
            potential security threats in real-time.
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}
