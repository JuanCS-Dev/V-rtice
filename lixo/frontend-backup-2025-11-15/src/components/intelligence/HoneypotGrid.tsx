"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Target,
  Activity,
  Signal,
  AlertCircle,
  CheckCircle,
} from "lucide-react";
import { formatTime } from "@/utils/dateHelpers";

interface HoneypotNode {
  id: string;
  name: string;
  type: "ssh" | "http" | "mysql" | "ftp" | "smb" | "rdp";
  status: "active" | "inactive" | "compromised" | "maintenance";
  interactionCount24h: number;
  credibilityScore: number;
  lastInteraction?: Date;
}

interface HoneypotGridProps {
  honeypots: HoneypotNode[];
  className?: string;
  onHoneypotClick?: (honeypot: HoneypotNode) => void;
}

const statusConfig = {
  active: {
    color: "bg-green-500",
    icon: CheckCircle,
    label: "Active",
    badgeVariant: "default" as const,
  },
  inactive: {
    color: "bg-gray-400",
    icon: Signal,
    label: "Inactive",
    badgeVariant: "secondary" as const,
  },
  compromised: {
    color: "bg-red-500",
    icon: AlertCircle,
    label: "Compromised",
    badgeVariant: "destructive" as const,
  },
  maintenance: {
    color: "bg-yellow-500",
    icon: Activity,
    label: "Maintenance",
    badgeVariant: "secondary" as const,
  },
};

const typeConfig = {
  ssh: { label: "SSH", color: "text-orange-600 dark:text-orange-400" },
  http: { label: "HTTP", color: "text-green-600 dark:text-green-400" },
  mysql: { label: "MySQL", color: "text-orange-600 dark:text-orange-400" },
  ftp: { label: "FTP", color: "text-red-600 dark:text-red-400" },
  smb: { label: "SMB", color: "text-pink-600 dark:text-pink-400" },
  rdp: { label: "RDP", color: "text-red-600 dark:text-red-400" },
};

/**
 * HoneypotGrid - Visual overview of deception infrastructure nodes
 *
 * Provides at-a-glance status of all deployed honeypots in the Reactive Fabric.
 * Critical for Phase 1 operational awareness: which nodes are active, credible, and attracting activity.
 *
 * Design Philosophy:
 * - Grid layout for density and scannability
 * - Status-driven visual hierarchy (compromised honeypots demand attention)
 * - Credibility score prominently displayed (Paradox of Realism monitoring)
 * - Interaction count shows "heat" of each node
 *
 * PAGANI Standards: Responsive grid, clear status indicators, interactive affordances.
 */
export const HoneypotGrid: React.FC<HoneypotGridProps> = ({
  honeypots,
  className = "",
  onHoneypotClick,
}) => {
  const getCredibilityColor = (score: number): string => {
    if (score >= 85) return "text-green-600 dark:text-green-400";
    if (score >= 70) return "text-yellow-600 dark:text-yellow-400";
    return "text-red-600 dark:text-red-400";
  };

  return (
    <Card className={`w-full ${className}`}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="h-5 w-5 text-primary" />
          Honeypot Infrastructure
          <Badge variant="outline" className="ml-auto">
            {honeypots.filter((h) => h.status === "active").length} /{" "}
            {honeypots.length} active
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[500px]">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {honeypots.length === 0 ? (
              <div className="col-span-full text-center py-8 text-gray-500 dark:text-gray-400">
                No honeypots deployed yet. Initialize the fabric...
              </div>
            ) : (
              honeypots.map((honeypot) => {
                const statusStyle = statusConfig[honeypot.status];
                const typeStyle = typeConfig[honeypot.type];
                const StatusIcon = statusStyle.icon;

                return (
                  <div
                    key={honeypot.id}
                    onClick={() => onHoneypotClick?.(honeypot)}
                    className={`
                      relative p-4 rounded-lg border-2
                      bg-white dark:bg-gray-800/50
                      ${
                        honeypot.status === "compromised"
                          ? "border-red-500 dark:border-red-600"
                          : "border-gray-200 dark:border-gray-700"
                      }
                      ${onHoneypotClick ? "cursor-pointer hover:shadow-lg hover:border-primary/50 transition-all" : ""}
                    `}
                  >
                    {/* Status indicator */}
                    <div className="absolute top-2 right-2">
                      <div
                        className={`w-3 h-3 rounded-full ${statusStyle.color} animate-pulse`}
                      />
                    </div>

                    {/* Header */}
                    <div className="mb-3">
                      <div className="flex items-center gap-2 mb-1">
                        <StatusIcon className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                        <span className="font-semibold text-gray-900 dark:text-white text-sm">
                          {honeypot.name}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge
                          variant="outline"
                          className={`text-xs ${typeStyle.color}`}
                        >
                          {typeStyle.label}
                        </Badge>
                        <Badge
                          variant={statusStyle.badgeVariant}
                          className="text-xs"
                        >
                          {statusStyle.label}
                        </Badge>
                      </div>
                    </div>

                    {/* Metrics */}
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600 dark:text-gray-400">
                          Interactions (24h)
                        </span>
                        <span className="font-bold text-gray-900 dark:text-white">
                          {honeypot.interactionCount24h}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600 dark:text-gray-400">
                          Credibility
                        </span>
                        <span
                          className={`font-bold ${getCredibilityColor(honeypot.credibilityScore)}`}
                        >
                          {honeypot.credibilityScore}%
                        </span>
                      </div>
                      {honeypot.lastInteraction && (
                        <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            Last: {formatTime(honeypot.lastInteraction, "N/A")}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

export default HoneypotGrid;
