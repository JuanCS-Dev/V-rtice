/**
 * ═══════════════════════════════════════════════════════════════════════════
 * SKELETON COMPONENT - CLAUDE.AI GREEN STYLE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * REESCRITO DO ZERO - NÃO é adaptação
 * Baseado em: Claude.ai loading skeletons
 * Estilo: Shimmer effect, subtle, clean
 */

import * as React from "react"
import { cn } from "@/lib/utils"
import "../../../styles/claude-design-green.css"

/**
 * Skeleton Component - Claude.ai Green Style
 *
 * Loading placeholder with shimmer animation
 *
 * Usage:
 * ```tsx
 * <Skeleton className="h-4 w-[250px]" />
 * <Skeleton className="h-12 w-12 rounded-full" />
 * ```
 */
function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        [
          "animate-pulse",
          "rounded-[var(--radius-md)]",
          "bg-[var(--muted)]",
          // Shimmer effect
          "relative overflow-hidden",
          "before:absolute before:inset-0",
          "before:-translate-x-full",
          "before:animate-[shimmer_2s_infinite]",
          "before:bg-gradient-to-r",
          "before:from-transparent",
          "before:via-white/10",
          "before:to-transparent",
        ].join(" "),
        className
      )}
      {...props}
    />
  )
}

/**
 * Card Skeleton - Common loading pattern
 */
function CardSkeleton() {
  return (
    <div
      className={cn([
        "bg-[var(--card)]",
        "border border-[var(--border)]",
        "rounded-[var(--radius-default)]",
        "p-[var(--space-6)]",
        "space-y-[var(--space-4)]",
      ].join(" "))}
    >
      <Skeleton className="h-6 w-[200px]" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-[300px]" />
      <div className="flex gap-[var(--space-2)]">
        <Skeleton className="h-10 w-[100px]" />
        <Skeleton className="h-10 w-[100px]" />
      </div>
    </div>
  )
}

/**
 * List Skeleton - For lists/tables
 */
function ListSkeleton({ items = 5 }: { items?: number }) {
  return (
    <div className="space-y-[var(--space-3)]">
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="flex items-center gap-[var(--space-4)]">
          <Skeleton className="h-12 w-12 rounded-full" />
          <div className="flex-1 space-y-[var(--space-2)]">
            <Skeleton className="h-4 w-[250px]" />
            <Skeleton className="h-3 w-[200px]" />
          </div>
        </div>
      ))}
    </div>
  )
}

export { Skeleton, CardSkeleton, ListSkeleton }
