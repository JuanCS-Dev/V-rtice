/**
 * ═══════════════════════════════════════════════════════════════════════════
 * LABEL COMPONENT - CLAUDE.AI GREEN STYLE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * REESCRITO DO ZERO - NÃO é adaptação
 * Baseado em: Claude.ai form labels
 * Estilo: Clean, readable, semantic
 */

import * as React from "react";
import * as LabelPrimitive from "@radix-ui/react-label";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import "../../../styles/claude-design-green.css";

const labelVariants = cva(
  [
    "text-[var(--text-sm)]",
    "font-[var(--font-primary)]",
    "font-medium",
    "leading-none",
    "peer-disabled:cursor-not-allowed",
    "peer-disabled:opacity-70",
  ].join(" "),
);

/**
 * Label Component - Claude.ai Green Style
 *
 * Clean form labels with proper accessibility
 *
 * Usage:
 * ```tsx
 * <Label htmlFor="email">Email</Label>
 * <Input id="email" type="email" />
 * ```
 */
const Label = React.forwardRef<
  React.ElementRef<typeof LabelPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof LabelPrimitive.Root> &
    VariantProps<typeof labelVariants>
>(({ className, ...props }, ref) => (
  <LabelPrimitive.Root
    ref={ref}
    className={cn(labelVariants(), className)}
    {...props}
  />
));

Label.displayName = LabelPrimitive.Root.displayName;

export { Label };
