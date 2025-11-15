/**
 * ═══════════════════════════════════════════════════════════════════════════
 * STAT CARD COMPONENT - CLAUDE.AI GREEN STYLE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * REESCRITO DO ZERO - NÃO é adaptação
 * Baseado em: Claude.ai metrics/stats display
 * Estilo: Clean, focused, verde accents
 */

import * as React from "react";
import { TrendingUp, TrendingDown, Minus, LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card } from "./card";
import { Badge } from "./badge";
import "../../../styles/claude-design-green.css";

export interface StatCardProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Stat title/label
   */
  title: string;
  /**
   * Main value
   */
  value: string | number;
  /**
   * Description/subtitle
   */
  description?: string;
  /**
   * Icon
   */
  icon?: React.ReactNode | LucideIcon;
  /**
   * Trend data
   */
  trend?: {
    value: number;
    label?: string;
    direction?: "up" | "down" | "neutral";
  };
  /**
   * Badge
   */
  badge?: {
    text: string;
    variant?: "default" | "success" | "warning" | "destructive";
  };
  /**
   * Loading state
   */
  loading?: boolean;
  /**
   * Variant
   */
  variant?: "default" | "success" | "warning" | "danger";
}

/**
 * StatCard Component - Claude.ai Green Style
 *
 * Clean stat/metric card for dashboards
 *
 * Usage:
 * ```tsx
 * <StatCard
 *   title="Total Users"
 *   value="1,234"
 *   trend={{ value: 12, direction: "up" }}
 *   icon={<Users />}
 * />
 * ```
 */
export const StatCard = React.forwardRef<HTMLDivElement, StatCardProps>(
  (
    {
      className,
      title,
      value,
      description,
      icon,
      trend,
      badge,
      loading = false,
      variant = "default",
      ...props
    },
    ref,
  ) => {
    // Auto-determine trend direction if not specified
    const trendDirection =
      trend?.direction ||
      (trend && trend.value > 0
        ? "up"
        : trend && trend.value < 0
          ? "down"
          : "neutral");

    const IconComponent = icon && typeof icon === "function" ? icon : null;

    const variantStyles = {
      default: "",
      success: "border-[var(--color-success)] bg-[var(--color-success-light)]",
      warning: "border-[var(--color-warning)] bg-[var(--color-warning-light)]",
      danger: "border-[var(--destructive)] bg-[var(--color-danger-light)]",
    };

    return (
      <Card
        ref={ref}
        className={cn(
          "relative overflow-hidden",
          variantStyles[variant],
          className,
        )}
        {...props}
      >
        <div className="p-[var(--space-6)]">
          {/* Header Row */}
          <div className="flex items-start justify-between mb-[var(--space-4)]">
            <div className="flex-1">
              {/* Title */}
              <p className="text-[var(--text-sm)] font-[var(--font-primary)] font-medium text-[var(--muted-foreground)] mb-[var(--space-1)]">
                {title}
              </p>

              {/* Value */}
              {loading ? (
                <div className="h-9 w-24 bg-[var(--muted)] rounded animate-pulse" />
              ) : (
                <p
                  className="text-[var(--text-3xl)] font-[var(--font-display)] font-bold"
                  style={{
                    color:
                      variant === "default" ? "var(--foreground)" : undefined,
                  }}
                >
                  {value}
                </p>
              )}
            </div>

            {/* Icon */}
            {icon && (
              <div
                className={cn(
                  [
                    "flex items-center justify-center",
                    "w-12 h-12",
                    "rounded-[var(--radius-default)]",
                    "bg-[var(--primary)]/10",
                    "text-[var(--primary)]",
                  ].join(" "),
                )}
              >
                {IconComponent ? <IconComponent className="w-6 h-6" /> : icon}
              </div>
            )}
          </div>

          {/* Footer Row */}
          <div className="flex items-center justify-between gap-[var(--space-2)]">
            {/* Trend */}
            {trend && !loading && (
              <div className="flex items-center gap-[var(--space-1)]">
                {trendDirection === "up" && (
                  <TrendingUp className="w-4 h-4 text-[var(--color-success)]" />
                )}
                {trendDirection === "down" && (
                  <TrendingDown className="w-4 h-4 text-[var(--destructive)]" />
                )}
                {trendDirection === "neutral" && (
                  <Minus className="w-4 h-4 text-[var(--muted-foreground)]" />
                )}

                <span
                  className={cn(
                    [
                      "text-[var(--text-sm)]",
                      "font-[var(--font-primary)]",
                      "font-medium",
                      trendDirection === "up" && "text-[var(--color-success)]",
                      trendDirection === "down" && "text-[var(--destructive)]",
                      trendDirection === "neutral" &&
                        "text-[var(--muted-foreground)]",
                    ].join(" "),
                  )}
                >
                  {trend.value > 0 ? "+" : ""}
                  {trend.value}%
                </span>

                {trend.label && (
                  <span className="text-[var(--text-sm)] font-[var(--font-primary)] text-[var(--muted-foreground)]">
                    {trend.label}
                  </span>
                )}
              </div>
            )}

            {/* Description */}
            {description && !trend && (
              <p className="text-[var(--text-sm)] font-[var(--font-primary)] text-[var(--muted-foreground)]">
                {description}
              </p>
            )}

            {/* Badge */}
            {badge && (
              <Badge variant={badge.variant || "default"}>{badge.text}</Badge>
            )}
          </div>
        </div>

        {/* Loading Overlay */}
        {loading && (
          <div className="absolute inset-0 bg-[var(--background)]/50 backdrop-blur-sm flex items-center justify-center">
            <div className="w-6 h-6 border-2 border-[var(--primary)] border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </Card>
    );
  },
);

StatCard.displayName = "StatCard";

/**
 * MetricCard - Simplified stat card
 */
export interface MetricCardProps
  extends Omit<StatCardProps, "trend" | "badge"> {
  subtitle?: string;
}

export const MetricCard = React.forwardRef<HTMLDivElement, MetricCardProps>(
  (
    {
      className,
      title,
      value,
      subtitle,
      icon,
      description,
      loading,
      variant,
      ...props
    },
    ref,
  ) => {
    return (
      <Card
        ref={ref}
        className={cn("p-[var(--space-6)]", className)}
        {...props}
      >
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-[var(--text-sm)] font-[var(--font-primary)] font-medium text-[var(--muted-foreground)]">
              {title}
            </p>
            {subtitle && (
              <p className="text-[var(--text-xs)] font-[var(--font-primary)] text-[var(--muted-foreground)] mt-0.5">
                {subtitle}
              </p>
            )}
            {loading ? (
              <div className="h-8 w-20 bg-[var(--muted)] rounded animate-pulse mt-2" />
            ) : (
              <p className="text-[var(--text-2xl)] font-[var(--font-display)] font-bold mt-2">
                {value}
              </p>
            )}
            {description && (
              <p className="text-[var(--text-sm)] font-[var(--font-primary)] text-[var(--muted-foreground)] mt-2">
                {description}
              </p>
            )}
          </div>
          {icon && (
            <div className="text-[var(--primary)]">
              {typeof icon === "function"
                ? React.createElement(icon, { className: "w-8 h-8" })
                : icon}
            </div>
          )}
        </div>
      </Card>
    );
  },
);

MetricCard.displayName = "MetricCard";

export { TrendingUp, TrendingDown, Minus };
