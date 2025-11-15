/**
 * ═══════════════════════════════════════════════════════════════════════════
 * SPINNER COMPONENT - CLAUDE.AI GREEN STYLE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * REESCRITO DO ZERO - NÃO é adaptação
 * Baseado em: Claude.ai loading spinners
 * Estilo: Clean, minimal spinner with verde accent
 */

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import "../../../styles/claude-design-green.css";

/**
 * Spinner Variants - Claude.ai style
 */
const spinnerVariants = cva(
  [
    "inline-block animate-spin rounded-[var(--radius-full)]",
    "border-2 border-solid border-current border-r-transparent",
  ].join(" "),
  {
    variants: {
      size: {
        sm: "h-4 w-4",
        default: "h-6 w-6",
        lg: "h-8 w-8",
        xl: "h-12 w-12",
      },
      variant: {
        default: "text-[var(--primary)]",
        secondary: "text-[var(--muted-foreground)]",
        light: "text-white",
        dark: "text-[var(--foreground)]",
      },
    },
    defaultVariants: {
      size: "default",
      variant: "default",
    },
  },
);

export interface SpinnerProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof spinnerVariants> {
  /**
   * Show loading text
   */
  label?: string;
}

/**
 * Spinner Component - Claude.ai Green Style
 *
 * Clean minimal loading spinner
 *
 * Usage:
 * ```tsx
 * <Spinner />
 * <Spinner size="lg" />
 * <Spinner variant="secondary" label="Loading..." />
 * ```
 */
function Spinner({ className, size, variant, label, ...props }: SpinnerProps) {
  return (
    <div
      className={cn("inline-flex items-center gap-[var(--space-2)]", className)}
      role="status"
      aria-label={label || "Loading"}
      {...props}
    >
      <div className={cn(spinnerVariants({ size, variant }))} />
      {label && (
        <span className="text-[var(--text-sm)] font-[var(--font-primary)] text-[var(--muted-foreground)]">
          {label}
        </span>
      )}
      <span className="sr-only">{label || "Loading"}</span>
    </div>
  );
}

/**
 * Loading Overlay - Full screen loading
 *
 * Usage:
 * ```tsx
 * <LoadingOverlay />
 * <LoadingOverlay message="Processando..." />
 * ```
 */
export interface LoadingOverlayProps {
  message?: string;
}

function LoadingOverlay({ message }: LoadingOverlayProps) {
  return (
    <div
      className={cn(
        [
          "fixed inset-0",
          "z-[var(--z-modal)]",
          "flex items-center justify-center",
          "bg-[var(--background)]/80",
          "backdrop-blur-[var(--blur-sm)]",
        ].join(" "),
      )}
      role="dialog"
      aria-modal="true"
      aria-label={message || "Loading"}
    >
      <div className="flex flex-col items-center gap-[var(--space-4)]">
        <Spinner size="xl" />
        {message && (
          <p className="text-[var(--text-lg)] font-[var(--font-primary)] text-[var(--foreground)]">
            {message}
          </p>
        )}
      </div>
    </div>
  );
}

export { Spinner, LoadingOverlay, spinnerVariants };
