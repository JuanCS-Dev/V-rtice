/**
 * ═══════════════════════════════════════════════════════════════════════════
 * BADGE COMPONENT - CLAUDE.AI GREEN STYLE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * REESCRITO DO ZERO - NÃO é adaptação
 * Baseado em: Claude.ai interface design
 * Estilo: Clean pills/badges with semantic colors
 * Primary: VERDE (#10b981)
 */

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import "../../../styles/claude-design-green.css";

/**
 * Badge Variants - Claude.ai Style
 *
 * Semantic colors with subtle backgrounds
 * - Default: Verde suave
 * - Success: Verde (naturally green)
 * - Warning: Amber
 * - Destructive: Red
 * - Secondary: Gray
 * - Outline: Border only
 */
const badgeVariants = cva(
  // Base styles - Clean pill
  [
    "inline-flex items-center",
    "rounded-[var(--radius-full)]",
    "border",
    "px-[var(--space-2-5)]",
    "py-[var(--space-1)]",
    "text-[var(--text-xs)]",
    "font-[var(--font-primary)]",
    "font-semibold",
    "transition-all duration-[var(--transition-fast)]",
    "focus:outline-none",
    "focus:ring-2",
    "focus:ring-[var(--ring)]",
    "focus:ring-offset-2",
  ].join(" "),
  {
    variants: {
      variant: {
        // Default - VERDE
        default: [
          "border-transparent",
          "bg-[var(--primary)]",
          "text-[var(--primary-foreground)]",
          "hover:bg-[var(--brand-green-hover)]",
        ].join(" "),

        // Success - Verde (já é verde naturalmente)
        success: [
          "border-transparent",
          "bg-[var(--color-success)]",
          "text-white",
          "hover:bg-[var(--color-success-hover)]",
        ].join(" "),

        // Warning - Amber
        warning: [
          "border-transparent",
          "bg-[var(--color-warning)]",
          "text-white",
          "hover:bg-[var(--color-warning-hover)]",
        ].join(" "),

        // Destructive - Red
        destructive: [
          "border-transparent",
          "bg-[var(--destructive)]",
          "text-[var(--destructive-foreground)]",
          "hover:bg-[var(--color-danger-hover)]",
        ].join(" "),

        // Info - Blue
        info: [
          "border-transparent",
          "bg-[var(--color-info)]",
          "text-white",
          "hover:bg-[var(--color-info-hover)]",
        ].join(" "),

        // Secondary - Gray
        secondary: [
          "border-transparent",
          "bg-[var(--secondary)]",
          "text-[var(--secondary-foreground)]",
          "hover:bg-[var(--secondary)]/80",
        ].join(" "),

        // Outline - Border only
        outline: [
          "border-[var(--border)]",
          "bg-transparent",
          "text-[var(--foreground)]",
          "hover:bg-[var(--muted)]",
        ].join(" "),

        // Subtle variants (light backgrounds)
        "success-subtle": [
          "border-[var(--color-success)]",
          "bg-[var(--color-success-light)]",
          "text-[var(--color-success)]",
          "hover:bg-[var(--color-success)]/20",
        ].join(" "),

        "warning-subtle": [
          "border-[var(--color-warning)]",
          "bg-[var(--color-warning-light)]",
          "text-[var(--color-warning)]",
          "hover:bg-[var(--color-warning)]/20",
        ].join(" "),

        "danger-subtle": [
          "border-[var(--color-danger)]",
          "bg-[var(--color-danger-light)]",
          "text-[var(--color-danger)]",
          "hover:bg-[var(--color-danger)]/20",
        ].join(" "),

        "info-subtle": [
          "border-[var(--color-info)]",
          "bg-[var(--color-info-light)]",
          "text-[var(--color-info)]",
          "hover:bg-[var(--color-info)]/20",
        ].join(" "),
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

/**
 * Badge Component - Claude.ai Green Style
 *
 * Clean semantic pills for status, labels, tags
 *
 * Usage:
 * ```tsx
 * <Badge>Default (Verde)</Badge>
 * <Badge variant="success">Success</Badge>
 * <Badge variant="warning">Warning</Badge>
 * <Badge variant="destructive">Error</Badge>
 * <Badge variant="success-subtle">Success Subtle</Badge>
 * ```
 */
function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
