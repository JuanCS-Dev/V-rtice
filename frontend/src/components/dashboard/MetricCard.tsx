import { Card } from "@/components/ui";
import type { ComponentType, SVGProps } from "react";

export interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: ComponentType<SVGProps<SVGSVGElement>>;
  iconColor?: string;
  trend?: "up" | "down" | "neutral";
  description?: string;
  isLoading?: boolean;
}

export function MetricCard({
  title,
  value,
  change,
  changeLabel,
  icon: Icon,
  iconColor = "text-primary-600",
  trend = "neutral",
  description,
  isLoading = false,
}: MetricCardProps) {
  const getTrendColor = () => {
    if (trend === "up") return "text-primary-600";
    if (trend === "down") return "text-red-600";
    return "text-[rgb(var(--text-secondary))]";
  };

  const getTrendSymbol = () => {
    if (trend === "up") return "↑";
    if (trend === "down") return "↓";
    return "•";
  };

  if (isLoading) {
    return (
      <Card variant="elevated" className="p-6">
        <div className="animate-pulse">
          <div className="flex items-center justify-between mb-3">
            <div className="h-3 bg-[rgb(var(--surface-tertiary))] rounded w-24" />
            {Icon && (
              <div className="h-4 w-4 bg-[rgb(var(--surface-tertiary))] rounded" />
            )}
          </div>
          <div className="h-8 bg-[rgb(var(--surface-tertiary))] rounded w-28 mb-2" />
          {(change !== undefined || description) && (
            <div className="h-2.5 bg-[rgb(var(--surface-tertiary))] rounded w-32" />
          )}
        </div>
      </Card>
    );
  }

  return (
    <Card
      variant="elevated"
      className="group p-6 transition-shadow duration-200 hover:shadow-lg"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-[rgb(var(--text-tertiary))]">
          {title}
        </p>
        {Icon && <Icon className={`h-4 w-4 ${iconColor}`} />}
      </div>

      {/* Value */}
      <div className="flex items-baseline gap-2 mb-1.5">
        <p className="text-3xl font-bold tracking-tight text-[rgb(var(--text-primary))]">
          {value}
        </p>
        {change !== undefined && (
          <span
            className={`flex items-center gap-0.5 text-sm font-medium ${getTrendColor()}`}
          >
            <span className="text-xs">{getTrendSymbol()}</span>
            {Math.abs(change)}%
          </span>
        )}
      </div>

      {/* Description */}
      {(changeLabel || description) && (
        <p className="text-xs text-[rgb(var(--text-tertiary))]">
          {changeLabel || description}
        </p>
      )}
    </Card>
  );
}
