/**
 * ═══════════════════════════════════════════════════════════════════════════
 * CARD COMPONENT - CLAUDE.AI GREEN STYLE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * REESCRITO DO ZERO - NÃO é adaptação
 * Baseado em: Claude.ai interface design
 * Estilo: Clean cards with subtle elevation
 * Hover: Subtle border color change (VERDE)
 */

import * as React from "react"
import { cn } from "@/lib/utils"
import "../../../styles/claude-design-green.css"

/**
 * Card - Base component
 *
 * Clean, minimal card with subtle shadow
 * Hover state changes border to verde
 */
const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      [
        // Base styles - Claude.ai clean card
        "bg-[var(--card)]",
        "text-[var(--card-foreground)]",
        "border border-[var(--border)]",
        "rounded-[var(--radius-default)]",
        "shadow-[var(--shadow-sm)]",
        // Transitions - smooth
        "transition-all duration-[var(--transition-normal)]",
        // Hover - subtle verde accent
        "hover:shadow-[var(--shadow-md)]",
        "hover:border-[var(--primary)]",
      ].join(" "),
      className
    )}
    {...props}
  />
))
Card.displayName = "Card"

/**
 * CardHeader - Top section of card
 *
 * Contains title and description
 * Clean spacing
 */
const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      [
        "flex flex-col",
        "space-y-[var(--space-2)]",
        "p-[var(--space-6)]",
      ].join(" "),
      className
    )}
    {...props}
  />
))
CardHeader.displayName = "CardHeader"

/**
 * CardTitle - Card heading
 *
 * Serif typography (Claude.ai style)
 * Clear hierarchy
 */
const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      [
        "text-[var(--text-2xl)]",
        "font-[var(--font-display)]",
        "font-semibold",
        "leading-[var(--leading-tight)]",
        "tracking-tight",
        "text-[var(--card-foreground)]",
      ].join(" "),
      className
    )}
    {...props}
  />
))
CardTitle.displayName = "CardTitle"

/**
 * CardDescription - Subtitle/description
 *
 * Muted color for secondary information
 */
const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn(
      [
        "text-[var(--text-sm)]",
        "font-[var(--font-primary)]",
        "text-[var(--muted-foreground)]",
        "leading-[var(--leading-normal)]",
      ].join(" "),
      className
    )}
    {...props}
  />
))
CardDescription.displayName = "CardDescription"

/**
 * CardContent - Main content area
 *
 * Clean padding, flexible content
 */
const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      [
        "p-[var(--space-6)]",
        "pt-0",
      ].join(" "),
      className
    )}
    {...props}
  />
))
CardContent.displayName = "CardContent"

/**
 * CardFooter - Footer section
 *
 * Typically contains actions/buttons
 */
const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      [
        "flex items-center",
        "p-[var(--space-6)]",
        "pt-0",
      ].join(" "),
      className
    )}
    {...props}
  />
))
CardFooter.displayName = "CardFooter"

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }
