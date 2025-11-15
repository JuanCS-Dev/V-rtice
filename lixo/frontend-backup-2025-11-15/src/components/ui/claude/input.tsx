/**
 * ═══════════════════════════════════════════════════════════════════════════
 * INPUT COMPONENT - CLAUDE.AI GREEN STYLE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * REESCRITO DO ZERO - NÃO é adaptação
 * Baseado em: Claude.ai interface design
 * Estilo: Clean, minimal, focused
 * Focus Color: VERDE (#10b981)
 */

import * as React from "react";
import { cn } from "@/lib/utils";
import "../../../styles/claude-design-green.css";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  /**
   * Error state
   */
  error?: boolean;
  /**
   * Success state
   */
  success?: boolean;
}

/**
 * Input Component - Claude.ai Green Style
 *
 * Features:
 * - Clean minimal design
 * - Verde focus ring
 * - Smooth transitions
 * - Serif typography (matches Claude.ai)
 * - Subtle shadows
 *
 * Usage:
 * ```tsx
 * <Input placeholder="Enter text..." />
 * <Input type="email" error />
 * <Input type="password" success />
 * ```
 */
const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, error, success, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          // Base styles - Claude.ai clean input
          [
            "flex h-10 w-full",
            "px-4 py-2",
            "text-[var(--text-base)]",
            "font-[var(--font-primary)]",
            "bg-[var(--background)]",
            "text-[var(--foreground)]",
            "border border-[var(--input)]",
            "rounded-[var(--radius-default)]",
            "shadow-[var(--shadow-xs)]",
            // Transitions
            "transition-all duration-[var(--transition-normal)]",
            // Placeholder
            "placeholder:text-[var(--muted-foreground)]",
            "placeholder:font-normal",
            // Focus - VERDE ring
            "focus-visible:outline-none",
            "focus-visible:ring-2",
            "focus-visible:ring-[var(--ring)]",
            "focus-visible:ring-offset-2",
            "focus-visible:border-[var(--primary)]",
            "focus-visible:shadow-[var(--shadow-sm)]",
            // Disabled
            "disabled:cursor-not-allowed",
            "disabled:opacity-50",
            "disabled:bg-[var(--muted)]",
            // File input
            "file:border-0",
            "file:bg-transparent",
            "file:text-[var(--text-sm)]",
            "file:font-medium",
            "file:text-[var(--foreground)]",
          ].join(" "),
          // Error state - Red
          error &&
            [
              "border-[var(--destructive)]",
              "focus-visible:ring-[var(--destructive)]",
              "text-[var(--color-danger-text)]",
            ].join(" "),
          // Success state - Verde
          success &&
            [
              "border-[var(--color-success)]",
              "focus-visible:ring-[var(--color-success)]",
              "text-[var(--color-success-text)]",
            ].join(" "),
          className,
        )}
        ref={ref}
        {...props}
      />
    );
  },
);

Input.displayName = "Input";

export { Input };
