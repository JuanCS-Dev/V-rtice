/**
 * ═══════════════════════════════════════════════════════════════════════════
 * BUTTON COMPONENT - CLAUDE.AI GREEN STYLE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * REESCRITO DO ZERO - NÃO é adaptação
 * Baseado em: Claude.ai interface design
 * Estilo: Clean, calm, subtle interactions
 * Primary Color: VERDE (#10b981)
 *
 * Design Philosophy:
 * - Subtle hover effects (não dramatic)
 * - Smooth transitions (Claude.ai style)
 * - Serif typography
 * - OKLCH colors
 * - Accessibility first
 */

import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import "../../../styles/claude-design-green.css"

/**
 * Button Variants - Claude.ai Style
 *
 * CRITICAL: Estilo minimalista, não aggressive
 * - Primary: Verde suave com hover sutil
 * - Secondary: Gray clean
 * - Ghost: Transparente com hover suave
 * - Outline: Border clean
 */
const buttonVariants = cva(
  // Base styles - Claude.ai clean button
  [
    "inline-flex items-center justify-center gap-2",
    "whitespace-nowrap",
    "font-medium",
    "transition-all",
    "focus-visible:outline-none",
    "focus-visible:ring-2",
    "disabled:pointer-events-none",
    "disabled:opacity-50",
    "cursor-pointer",
    // Typography - Serif (Claude.ai style)
    "font-[var(--font-primary)]",
  ].join(" "),
  {
    variants: {
      variant: {
        // Primary - VERDE (Claude.ai CTA style)
        default: [
          "bg-[var(--primary)]",
          "text-[var(--primary-foreground)]",
          "shadow-[var(--shadow-sm)]",
          "hover:bg-[var(--brand-green-hover)]",
          "hover:shadow-[var(--shadow-md)]",
          "hover:-translate-y-0.5",
          "active:translate-y-0",
          "active:shadow-[var(--shadow-sm)]",
          "focus-visible:ring-[var(--ring)]",
        ].join(" "),

        // Destructive - Red (subtle)
        destructive: [
          "bg-[var(--destructive)]",
          "text-[var(--destructive-foreground)]",
          "shadow-[var(--shadow-sm)]",
          "hover:bg-[var(--color-danger-hover)]",
          "hover:shadow-[var(--shadow-md)]",
          "focus-visible:ring-[var(--destructive)]",
        ].join(" "),

        // Outline - Clean border
        outline: [
          "border border-[var(--border)]",
          "bg-transparent",
          "text-[var(--foreground)]",
          "hover:bg-[var(--muted)]",
          "hover:border-[var(--primary)]",
          "hover:text-[var(--primary)]",
          "focus-visible:ring-[var(--ring)]",
        ].join(" "),

        // Secondary - Clean gray
        secondary: [
          "bg-[var(--secondary)]",
          "text-[var(--secondary-foreground)]",
          "hover:bg-[var(--secondary)]/80",
          "shadow-[var(--shadow-xs)]",
          "focus-visible:ring-[var(--ring)]",
        ].join(" "),

        // Ghost - Minimal
        ghost: [
          "bg-transparent",
          "text-[var(--foreground)]",
          "hover:bg-[var(--muted)]",
          "hover:text-[var(--foreground)]",
          "focus-visible:ring-[var(--ring)]",
        ].join(" "),

        // Link - Underline style
        link: [
          "text-[var(--primary)]",
          "underline-offset-4",
          "hover:underline",
          "hover:text-[var(--brand-green-hover)]",
          "focus-visible:ring-[var(--ring)]",
        ].join(" "),
      },
      size: {
        default: [
          "h-10",
          "px-6",
          "py-3",
          "text-[var(--text-base)]",
          "rounded-[var(--radius-default)]",
        ].join(" "),

        sm: [
          "h-9",
          "px-4",
          "py-2",
          "text-[var(--text-sm)]",
          "rounded-[var(--radius-md)]",
        ].join(" "),

        lg: [
          "h-11",
          "px-8",
          "py-4",
          "text-[var(--text-lg)]",
          "rounded-[var(--radius-lg)]",
        ].join(" "),

        icon: [
          "h-10",
          "w-10",
          "p-0",
          "rounded-[var(--radius-default)]",
        ].join(" "),
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

/**
 * Button Component - Claude.ai Green Style
 *
 * Usage:
 * ```tsx
 * <Button>Primary Action</Button>
 * <Button variant="secondary">Secondary</Button>
 * <Button variant="ghost">Ghost</Button>
 * <Button variant="outline">Outline</Button>
 * <Button size="sm">Small</Button>
 * <Button size="lg">Large</Button>
 * ```
 */
const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"

    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)

Button.displayName = "Button"

export { Button, buttonVariants }
