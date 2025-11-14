/**
 * ═══════════════════════════════════════════════════════════════════════════
 * CONTAINER & GRID COMPONENTS - CLAUDE.AI GREEN STYLE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * REESCRITO DO ZERO - NÃO é adaptação
 * Baseado em: Claude.ai layout patterns
 * Estilo: Clean, responsive, centered
 */

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import "../../../styles/claude-design-green.css"

/**
 * Container Variants
 */
const containerVariants = cva(
  [
    "w-full mx-auto",
    "px-[var(--space-4)]",
  ].join(" "),
  {
    variants: {
      size: {
        sm: "max-w-[640px]",
        md: "max-w-[768px]",
        lg: "max-w-[1024px]",
        xl: "max-w-[1280px]",
        "2xl": "max-w-[1536px]",
        full: "max-w-full",
      },
      padding: {
        none: "px-0",
        sm: "px-[var(--space-2)]",
        md: "px-[var(--space-4)]",
        lg: "px-[var(--space-6)]",
        xl: "px-[var(--space-8)]",
      },
    },
    defaultVariants: {
      size: "xl",
      padding: "md",
    },
  }
)

export interface ContainerProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof containerVariants> {}

/**
 * Container Component - Claude.ai Style
 *
 * Responsive centered container
 *
 * Usage:
 * ```tsx
 * <Container>Content</Container>
 * <Container size="lg">Smaller content</Container>
 * ```
 */
export const Container = React.forwardRef<HTMLDivElement, ContainerProps>(
  ({ className, size, padding, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(containerVariants({ size, padding, className }))}
        {...props}
      />
    )
  }
)

Container.displayName = "Container"

/**
 * Grid Variants
 */
const gridVariants = cva(
  [
    "grid",
  ].join(" "),
  {
    variants: {
      cols: {
        1: "grid-cols-1",
        2: "grid-cols-1 md:grid-cols-2",
        3: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
        4: "grid-cols-1 md:grid-cols-2 lg:grid-cols-4",
        6: "grid-cols-2 md:grid-cols-3 lg:grid-cols-6",
        12: "grid-cols-12",
      },
      gap: {
        none: "gap-0",
        sm: "gap-[var(--space-2)]",
        md: "gap-[var(--space-4)]",
        lg: "gap-[var(--space-6)]",
        xl: "gap-[var(--space-8)]",
      },
    },
    defaultVariants: {
      cols: 1,
      gap: "md",
    },
  }
)

export interface GridProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof gridVariants> {}

/**
 * Grid Component - Claude.ai Style
 *
 * Responsive grid layout
 *
 * Usage:
 * ```tsx
 * <Grid cols={3} gap="lg">
 *   <Card>Item 1</Card>
 *   <Card>Item 2</Card>
 *   <Card>Item 3</Card>
 * </Grid>
 * ```
 */
export const Grid = React.forwardRef<HTMLDivElement, GridProps>(
  ({ className, cols, gap, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(gridVariants({ cols, gap, className }))}
        {...props}
      />
    )
  }
)

Grid.displayName = "Grid"

/**
 * Stack Component - Vertical layout with gap
 */
export interface StackProps extends React.HTMLAttributes<HTMLDivElement> {
  gap?: "none" | "sm" | "md" | "lg" | "xl"
  align?: "start" | "center" | "end" | "stretch"
}

export const Stack = React.forwardRef<HTMLDivElement, StackProps>(
  ({ className, gap = "md", align = "stretch", ...props }, ref) => {
    const gapClass = {
      none: "gap-0",
      sm: "gap-[var(--space-2)]",
      md: "gap-[var(--space-4)]",
      lg: "gap-[var(--space-6)]",
      xl: "gap-[var(--space-8)]",
    }[gap]

    const alignClass = {
      start: "items-start",
      center: "items-center",
      end: "items-end",
      stretch: "items-stretch",
    }[align]

    return (
      <div
        ref={ref}
        className={cn("flex flex-col", gapClass, alignClass, className)}
        {...props}
      />
    )
  }
)

Stack.displayName = "Stack"

/**
 * Inline Component - Horizontal layout with gap
 */
export interface InlineProps extends React.HTMLAttributes<HTMLDivElement> {
  gap?: "none" | "sm" | "md" | "lg" | "xl"
  align?: "start" | "center" | "end" | "stretch"
  justify?: "start" | "center" | "end" | "between" | "around"
  wrap?: boolean
}

export const Inline = React.forwardRef<HTMLDivElement, InlineProps>(
  (
    {
      className,
      gap = "md",
      align = "center",
      justify = "start",
      wrap = false,
      ...props
    },
    ref
  ) => {
    const gapClass = {
      none: "gap-0",
      sm: "gap-[var(--space-2)]",
      md: "gap-[var(--space-4)]",
      lg: "gap-[var(--space-6)]",
      xl: "gap-[var(--space-8)]",
    }[gap]

    const alignClass = {
      start: "items-start",
      center: "items-center",
      end: "items-end",
      stretch: "items-stretch",
    }[align]

    const justifyClass = {
      start: "justify-start",
      center: "justify-center",
      end: "justify-end",
      between: "justify-between",
      around: "justify-around",
    }[justify]

    return (
      <div
        ref={ref}
        className={cn(
          "flex",
          gapClass,
          alignClass,
          justifyClass,
          wrap && "flex-wrap",
          className
        )}
        {...props}
      />
    )
  }
)

Inline.displayName = "Inline"

/**
 * Section Component - Page section with spacing
 */
export interface SectionProps extends React.HTMLAttributes<HTMLElement> {
  spacing?: "none" | "sm" | "md" | "lg" | "xl"
}

export const Section = React.forwardRef<HTMLElement, SectionProps>(
  ({ className, spacing = "lg", ...props }, ref) => {
    const spacingClass = {
      none: "py-0",
      sm: "py-[var(--space-4)]",
      md: "py-[var(--space-8)]",
      lg: "py-[var(--space-12)]",
      xl: "py-[var(--space-16)]",
    }[spacing]

    return (
      <section
        ref={ref}
        className={cn(spacingClass, className)}
        {...props}
      />
    )
  }
)

Section.displayName = "Section"

export { containerVariants, gridVariants }
