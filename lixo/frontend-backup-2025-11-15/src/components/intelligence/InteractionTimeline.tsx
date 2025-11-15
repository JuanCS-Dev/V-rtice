"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Clock, MapPin, User, Shield, AlertTriangle } from "lucide-react";
import { formatTime } from "@/utils/dateHelpers";

interface InteractionEvent {
  id: string;
  timestamp: Date;
  honeypotId: string;
  honeypotName: string;
  sourceIp: string;
  sourceCountry: string;
  interactionType: "scan" | "probe" | "exploit" | "enumeration";
  severity: "low" | "medium" | "high" | "critical";
  ttpsDetected: string[];
}

interface InteractionTimelineProps {
  events: InteractionEvent[];
  className?: string;
  maxHeight?: string;
}

const severityConfig = {
  low: { color: "bg-orange-500", variant: "secondary" as const },
  medium: { color: "bg-yellow-500", variant: "secondary" as const },
  high: { color: "bg-orange-500", variant: "destructive" as const },
  critical: { color: "bg-red-600", variant: "destructive" as const },
};

const interactionTypeConfig = {
  scan: { label: "Port Scan", icon: Shield },
  probe: { label: "Service Probe", icon: AlertTriangle },
  exploit: { label: "Exploit Attempt", icon: AlertTriangle },
  enumeration: { label: "Enumeration", icon: User },
};

/**
 * InteractionTimeline - Real-time view of honeypot interactions
 *
 * Provides chronological visualization of attacker interactions with deception infrastructure.
 * Critical for Phase 1 intelligence collection: every interaction is a datapoint for TTP analysis.
 *
 * Design Principles:
 * - Chronological clarity: Most recent first
 * - Severity-based visual hierarchy
 * - TTP attribution visible at glance
 * - Geographic context (source tracking)
 *
 * PAGANI Compliance: Scrollable, responsive, information-dense without clutter.
 */
export const InteractionTimeline: React.FC<InteractionTimelineProps> = ({
  events,
  className = "",
  maxHeight = "h-96",
}) => {
  return (
    <Card className={`w-full ${className}`}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-primary" />
          Interaction Timeline
          <Badge variant="outline" className="ml-auto">
            {events.length} events
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className={maxHeight}>
          <div className="space-y-4">
            {events.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                No interactions detected yet. The fabric is monitoring...
              </div>
            ) : (
              events.map((event, index) => {
                const severityStyle = severityConfig[event.severity];
                const interactionType =
                  interactionTypeConfig[event.interactionType];
                const Icon = interactionType.icon;

                return (
                  <div
                    key={event.id}
                    className="relative pl-6 pb-4 border-l-2 border-gray-300 dark:border-gray-700 last:border-l-0 last:pb-0"
                  >
                    {/* Timeline dot */}
                    <div
                      className={`absolute left-[-9px] top-0 w-4 h-4 rounded-full ${severityStyle.color} border-2 border-white dark:border-gray-900`}
                    />

                    <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                      {/* Header */}
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Icon className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                          <span className="font-medium text-gray-900 dark:text-white">
                            {interactionType.label}
                          </span>
                          <Badge
                            variant={severityStyle.variant}
                            className="text-xs"
                          >
                            {event.severity}
                          </Badge>
                        </div>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {formatTime(event.timestamp, "N/A")}
                        </span>
                      </div>

                      {/* Target Info */}
                      <div className="text-sm space-y-1 mb-3">
                        <div className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
                          <Shield className="h-3 w-3" />
                          <span className="font-mono text-xs">
                            {event.honeypotName}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                          <User className="h-3 w-3" />
                          <span className="font-mono text-xs">
                            {event.sourceIp}
                          </span>
                          <MapPin className="h-3 w-3 ml-2" />
                          <span className="text-xs">{event.sourceCountry}</span>
                        </div>
                      </div>

                      {/* TTPs Detected */}
                      {event.ttpsDetected.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {event.ttpsDetected.map((ttp, idx) => (
                            <Badge
                              key={idx}
                              variant="outline"
                              className="text-xs font-mono bg-primary/5"
                            >
                              {ttp}
                            </Badge>
                          ))}
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

export default InteractionTimeline;
