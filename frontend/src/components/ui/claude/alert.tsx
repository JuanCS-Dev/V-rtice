/**
 * ═══════════════════════════════════════════════════════════════════════════
 * ALERT COMPONENT - CLAUDE.AI GREEN STYLE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * REESCRITO DO ZERO - NÃO é adaptação
 * Baseado em: Claude.ai notifications/alerts
 * Estilo: Clean, semantic feedback with verde success
 */

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { AlertCircle, CheckCircle2, Info, AlertTriangle, X } from "lucide-react"
import { cn } from "@/lib/utils"
import "../../../styles/claude-design-green.css"

/**
 * Alert Variants - Claude.ai style semantic alerts
 */
const alertVariants = cva(
  [
    "relative w-full",
    "rounded-[var(--radius-default)]",
    "border",
    "p-[var(--space-4)]",
    "font-[var(--font-primary)]",
    "transition-all duration-[var(--transition-normal)]",
  ].join(" "),
  {
    variants: {
      variant: {
        default: [
          "bg-[var(--background)]",
          "border-[var(--border)]",
          "text-[var(--foreground)]",
        ].join(" "),

        // Success - VERDE
        success: [
          "bg-[var(--color-success-light)]",
          "border-[var(--color-success)]",
          "text-[var(--color-success)]",
          "[&>svg]:text-[var(--color-success)]",
        ].join(" "),

        // Warning - Amber
        warning: [
          "bg-[var(--color-warning-light)]",
          "border-[var(--color-warning)]",
          "text-[var(--color-warning)]",
          "[&>svg]:text-[var(--color-warning)]",
        ].join(" "),

        // Error/Destructive - Red
        destructive: [
          "bg-[var(--color-danger-light)]",
          "border-[var(--destructive)]",
          "text-[var(--destructive)]",
          "[&>svg]:text-[var(--destructive)]",
        ].join(" "),

        // Info - Blue
        info: [
          "bg-[var(--color-info-light)]",
          "border-[var(--color-info)]",
          "text-[var(--color-info)]",
          "[&>svg]:text-[var(--color-info)]",
        ].join(" "),
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

/**
 * Alert Icon mapping
 */
const alertIcons = {
  default: Info,
  success: CheckCircle2,
  warning: AlertTriangle,
  destructive: AlertCircle,
  info: Info,
}

export interface AlertProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof alertVariants> {
  /**
   * Show close button
   */
  dismissible?: boolean
  /**
   * On dismiss callback
   */
  onDismiss?: () => void
  /**
   * Custom icon (overrides default)
   */
  icon?: React.ReactNode
}

/**
 * Alert Component - Claude.ai Green Style
 *
 * Semantic feedback alerts with verde success state
 *
 * Usage:
 * ```tsx
 * <Alert variant="success">
 *   <AlertTitle>Success!</AlertTitle>
 *   <AlertDescription>Your changes have been saved.</AlertDescription>
 * </Alert>
 *
 * <Alert variant="warning" dismissible onDismiss={() => {}}>
 *   <AlertDescription>Warning message here.</AlertDescription>
 * </Alert>
 * ```
 */
const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant, dismissible, onDismiss, icon, children, ...props }, ref) => {
    const [dismissed, setDismissed] = React.useState(false)

    const Icon = variant ? alertIcons[variant] : alertIcons.default

    const handleDismiss = () => {
      setDismissed(true)
      onDismiss?.()
    }

    if (dismissed) return null

    return (
      <div
        ref={ref}
        role="alert"
        className={cn(alertVariants({ variant }), className)}
        {...props}
      >
        <div className="flex gap-[var(--space-3)]">
          {/* Icon */}
          <div className="shrink-0 mt-0.5">
            {icon || <Icon className="h-5 w-5" />}
          </div>

          {/* Content */}
          <div className="flex-1 [&_p]:leading-relaxed">
            {children}
          </div>

          {/* Dismiss button */}
          {dismissible && (
            <button
              onClick={handleDismiss}
              className={cn([
                "shrink-0",
                "rounded-[var(--radius-sm)]",
                "p-1",
                "opacity-70 hover:opacity-100",
                "transition-opacity duration-[var(--transition-fast)]",
                "focus:outline-none",
                "focus:ring-2",
                "focus:ring-[var(--ring)]",
              ].join(" "))}
              aria-label="Dismiss"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    )
  }
)
Alert.displayName = "Alert"

/**
 * Alert Title
 */
const AlertTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h5
    ref={ref}
    className={cn(
      [
        "mb-[var(--space-1)]",
        "font-medium",
        "text-[var(--text-base)]",
        "leading-none",
        "tracking-tight",
      ].join(" "),
      className
    )}
    {...props}
  />
))
AlertTitle.displayName = "AlertTitle"

/**
 * Alert Description
 */
const AlertDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      [
        "text-[var(--text-sm)]",
        "[&_p]:leading-relaxed",
      ].join(" "),
      className
    )}
    {...props}
  />
))
AlertDescription.displayName = "AlertDescription"

export { Alert, AlertTitle, AlertDescription, alertVariants }
