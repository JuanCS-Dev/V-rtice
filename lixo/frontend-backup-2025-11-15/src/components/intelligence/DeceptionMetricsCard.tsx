"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity, Shield, Target, TrendingUp } from "lucide-react";

interface MetricItemProps {
  label: string;
  value: string | number;
  trend?: "up" | "down" | "neutral";
  icon: React.ReactNode;
}

const MetricItem: React.FC<MetricItemProps> = ({
  label,
  value,
  trend,
  icon,
}) => (
  <div className="flex items-center justify-between p-4 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
    <div className="flex items-center gap-3">
      <div className="p-2 rounded-md bg-primary/10 text-primary">{icon}</div>
      <div>
        <p className="text-sm text-gray-600 dark:text-gray-400">{label}</p>
        <p className="text-2xl font-bold text-gray-900 dark:text-white">
          {value}
        </p>
      </div>
    </div>
    {trend && (
      <Badge
        variant={
          trend === "up"
            ? "default"
            : trend === "down"
              ? "destructive"
              : "secondary"
        }
        className="ml-2"
      >
        <TrendingUp className="h-3 w-3 mr-1" />
        {trend}
      </Badge>
    )}
  </div>
);

interface DeceptionMetricsCardProps {
  metrics: {
    activeHoneypots: number;
    interactionsToday: number;
    threatsDetected: number;
    credibilityScore: number;
  };
  className?: string;
}

/**
 * DeceptionMetricsCard - High-level metrics for deception infrastructure
 *
 * Displays key performance indicators for the Reactive Fabric:
 * - Active honeypot count
 * - Interaction metrics
 * - Threat detection rate
 * - Credibility score (Paradox of Realism compliance)
 *
 * Design Philosophy: Clarity over complexity. Each metric tells a story.
 * Aligned with PAGANI standards: clean, purposeful, responsive.
 */
export const DeceptionMetricsCard: React.FC<DeceptionMetricsCardProps> = ({
  metrics,
  className = "",
}) => {
  return (
    <Card className={`w-full ${className}`}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-primary" />
          Deception Metrics
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <MetricItem
            label="Active Honeypots"
            value={metrics.activeHoneypots}
            icon={<Target className="h-5 w-5" />}
            trend="neutral"
          />
          <MetricItem
            label="Interactions (24h)"
            value={metrics.interactionsToday}
            icon={<Activity className="h-5 w-5" />}
            trend="up"
          />
          <MetricItem
            label="Threats Detected"
            value={metrics.threatsDetected}
            icon={<Shield className="h-5 w-5" />}
            trend="up"
          />
          <MetricItem
            label="Credibility Score"
            value={`${metrics.credibilityScore}%`}
            icon={<TrendingUp className="h-5 w-5" />}
            trend={metrics.credibilityScore >= 85 ? "up" : "neutral"}
          />
        </div>
      </CardContent>
    </Card>
  );
};

export default DeceptionMetricsCard;
