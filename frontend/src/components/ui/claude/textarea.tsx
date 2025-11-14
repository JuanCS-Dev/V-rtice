/**
 * ═══════════════════════════════════════════════════════════════════════════
 * TEXTAREA COMPONENT - CLAUDE.AI GREEN STYLE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * REESCRITO DO ZERO - NÃO é adaptação
 * Baseado em: Claude.ai chat input style
 * Estilo: Clean, minimal, focused, resizable
 * Focus Color: VERDE (#10b981)
 */

import * as React from "react"
import { cn } from "@/lib/utils"
import "../../../styles/claude-design-green.css"

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  /**
   * Error state
   */
  error?: boolean
  /**
   * Success state
   */
  success?: boolean
}

/**
 * Textarea Component - Claude.ai Green Style
 *
 * Features:
 * - Clean minimal design (Claude.ai chat style)
 * - Verde focus ring
 * - Auto-resize capable
 * - Smooth transitions
 * - Serif typography
 *
 * Usage:
 * ```tsx
 * <Textarea placeholder="Enter your message..." rows={4} />
 * <Textarea error />
 * <Textarea success />
 * ```
 */
const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, success, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          // Base styles - Claude.ai clean textarea
          [
            "flex min-h-[80px] w-full",
            "px-4 py-3",
            "text-[var(--text-base)]",
            "font-[var(--font-primary)]",
            "bg-[var(--background)]",
            "text-[var(--foreground)]",
            "border border-[var(--input)]",
            "rounded-[var(--radius-default)]",
            "shadow-[var(--shadow-xs)]",
            // Resize
            "resize-y",
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
            "disabled:resize-none",
          ].join(" "),
          // Error state - Red
          error && [
            "border-[var(--destructive)]",
            "focus-visible:ring-[var(--destructive)]",
            "text-[var(--color-danger-text)]",
          ].join(" "),
          // Success state - Verde
          success && [
            "border-[var(--color-success)]",
            "focus-visible:ring-[var(--color-success)]",
            "text-[var(--color-success-text)]",
          ].join(" "),
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)

Textarea.displayName = "Textarea"

export { Textarea }
