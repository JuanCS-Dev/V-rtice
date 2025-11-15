/**
 * ═══════════════════════════════════════════════════════════════════════════
 * SWITCH COMPONENT - CLAUDE.AI GREEN STYLE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * REESCRITO DO ZERO - NÃO é adaptação
 * Baseado em: Claude.ai toggles
 * Estilo: Clean toggle with verde active state
 */

import * as React from "react"
import * as SwitchPrimitives from "@radix-ui/react-switch"
import { cn } from "@/lib/utils"
import "../../../styles/claude-design-green.css"

/**
 * Switch Component - Claude.ai Green Style
 *
 * Clean toggle switch with verde active state
 *
 * Usage:
 * ```tsx
 * <Switch checked={enabled} onCheckedChange={setEnabled} />
 * <Switch disabled />
 * ```
 */
const Switch = React.forwardRef<
  React.ElementRef<typeof SwitchPrimitives.Root>,
  React.ComponentPropsWithoutRef<typeof SwitchPrimitives.Root>
>(({ className, ...props }, ref) => (
  <SwitchPrimitives.Root
    className={cn(
      [
        "peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center",
        "rounded-[var(--radius-full)]",
        "border-2 border-transparent",
        "shadow-[var(--shadow-sm)]",
        "transition-all duration-[var(--transition-normal)]",
        // Focus
        "focus-visible:outline-none",
        "focus-visible:ring-2",
        "focus-visible:ring-[var(--ring)]",
        "focus-visible:ring-offset-2",
        // Disabled
        "disabled:cursor-not-allowed",
        "disabled:opacity-50",
        // Unchecked state
        "bg-[var(--input)]",
        // Checked state - VERDE
        "data-[state=checked]:bg-[var(--primary)]",
        "data-[state=checked]:shadow-[var(--shadow-glow-green-soft)]",
      ].join(" "),
      className
    )}
    {...props}
    ref={ref}
  >
    <SwitchPrimitives.Thumb
      className={cn(
        [
          "pointer-events-none block h-5 w-5",
          "rounded-[var(--radius-full)]",
          "bg-[var(--background)]",
          "shadow-[var(--shadow-md)]",
          "ring-0",
          "transition-transform duration-[var(--transition-normal)]",
          "data-[state=checked]:translate-x-5",
          "data-[state=unchecked]:translate-x-0",
        ].join(" ")
      )}
    />
  </SwitchPrimitives.Root>
))
Switch.displayName = SwitchPrimitives.Root.displayName

export { Switch }
