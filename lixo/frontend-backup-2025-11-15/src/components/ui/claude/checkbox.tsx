/**
 * ═══════════════════════════════════════════════════════════════════════════
 * CHECKBOX COMPONENT - CLAUDE.AI GREEN STYLE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * REESCRITO DO ZERO - NÃO é adaptação
 * Baseado em: Claude.ai checkboxes
 * Estilo: Clean checkbox with verde checked state
 */

import * as React from "react";
import * as CheckboxPrimitive from "@radix-ui/react-checkbox";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import "../../../styles/claude-design-green.css";

/**
 * Checkbox Component - Claude.ai Green Style
 *
 * Clean checkbox with verde checked state
 *
 * Usage:
 * ```tsx
 * <Checkbox checked={agreed} onCheckedChange={setAgreed} />
 * <Checkbox disabled />
 * ```
 */
const Checkbox = React.forwardRef<
  React.ElementRef<typeof CheckboxPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof CheckboxPrimitive.Root>
>(({ className, ...props }, ref) => (
  <CheckboxPrimitive.Root
    ref={ref}
    className={cn(
      [
        "peer h-5 w-5 shrink-0",
        "rounded-[var(--radius-sm)]",
        "border border-[var(--input)]",
        "shadow-[var(--shadow-xs)]",
        "transition-all duration-[var(--transition-fast)]",
        // Focus
        "focus-visible:outline-none",
        "focus-visible:ring-2",
        "focus-visible:ring-[var(--ring)]",
        "focus-visible:ring-offset-2",
        // Disabled
        "disabled:cursor-not-allowed",
        "disabled:opacity-50",
        // Checked state - VERDE
        "data-[state=checked]:bg-[var(--primary)]",
        "data-[state=checked]:border-[var(--primary)]",
        "data-[state=checked]:text-[var(--primary-foreground)]",
        // Hover
        "hover:border-[var(--primary)]",
      ].join(" "),
      className,
    )}
    {...props}
  >
    <CheckboxPrimitive.Indicator
      className={cn("flex items-center justify-center text-current")}
    >
      <Check className="h-4 w-4" />
    </CheckboxPrimitive.Indicator>
  </CheckboxPrimitive.Root>
));
Checkbox.displayName = CheckboxPrimitive.Root.displayName;

export { Checkbox };
