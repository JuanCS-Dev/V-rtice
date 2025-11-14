/**
 * ═══════════════════════════════════════════════════════════════════════════
 * PAGE TRANSITION - CLAUDE.AI GREEN STYLE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Smooth page transitions para SPA routing
 * Baseado em: Claude.ai subtle animations
 *
 * Usage com React Router:
 * ```tsx
 * <PageTransition>
 *   <YourPage />
 * </PageTransition>
 * ```
 */

import * as React from "react"
import { cn } from "@/lib/utils"
import "../../../styles/claude-animations.css"

export interface PageTransitionProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Transition type
   */
  type?: "fade" | "slide" | "scale" | "slide-fade"
  /**
   * Transition duration in ms
   */
  duration?: number
  /**
   * Delay before transition starts
   */
  delay?: number
  /**
   * Children to animate
   */
  children: React.ReactNode
}

/**
 * PageTransition Component
 *
 * Wraps page content with smooth enter/exit animations
 *
 * Usage:
 * ```tsx
 * <PageTransition type="slide-fade">
 *   <Dashboard />
 * </PageTransition>
 * ```
 */
export const PageTransition = React.forwardRef<HTMLDivElement, PageTransitionProps>(
  ({ className, type = "fade", duration = 400, delay = 0, children, ...props }, ref) => {
    const [isVisible, setIsVisible] = React.useState(false)

    React.useEffect(() => {
      // Trigger animation on mount
      const timer = setTimeout(() => {
        setIsVisible(true)
      }, delay)

      return () => clearTimeout(timer)
    }, [delay])

    const animationClass = React.useMemo(() => {
      switch (type) {
        case "fade":
          return "page-enter"
        case "slide":
          return "page-slide-enter"
        case "scale":
          return "animate-scale-in"
        case "slide-fade":
          return "page-slide-enter"
        default:
          return "page-enter"
      }
    }, [type])

    return (
      <div
        ref={ref}
        className={cn(
          [
            // Base
            "w-full",
            // Animation
            isVisible && animationClass,
          ].join(" "),
          className
        )}
        style={{
          animationDuration: `${duration}ms`,
        }}
        {...props}
      >
        {children}
      </div>
    )
  }
)

PageTransition.displayName = "PageTransition"

/* ============================================================================
   SCROLL REVEAL
   ============================================================================ */

export interface ScrollRevealProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Reveal type
   */
  type?: "fade" | "slide-up" | "slide-left" | "slide-right"
  /**
   * Threshold for IntersectionObserver (0-1)
   */
  threshold?: number
  /**
   * Root margin for IntersectionObserver
   */
  rootMargin?: string
  /**
   * Trigger animation once or every time element enters viewport
   */
  once?: boolean
  /**
   * Stagger delay (for sequential animations)
   */
  stagger?: number
  /**
   * Children to animate
   */
  children: React.ReactNode
}

/**
 * ScrollReveal Component
 *
 * Reveals content when scrolled into view
 *
 * Usage:
 * ```tsx
 * <ScrollReveal type="slide-up">
 *   <Card>Content revealed on scroll</Card>
 * </ScrollReveal>
 * ```
 */
export const ScrollReveal = React.forwardRef<HTMLDivElement, ScrollRevealProps>(
  (
    {
      className,
      type = "fade",
      threshold = 0.1,
      rootMargin = "0px",
      once = true,
      stagger = 0,
      children,
      ...props
    },
    ref
  ) => {
    const [isVisible, setIsVisible] = React.useState(false)
    const elementRef = React.useRef<HTMLDivElement>(null)

    // Combine refs
    React.useImperativeHandle(ref, () => elementRef.current as HTMLDivElement)

    React.useEffect(() => {
      const element = elementRef.current
      if (!element) return

      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            setIsVisible(true)
            if (once) {
              observer.unobserve(element)
            }
          } else if (!once) {
            setIsVisible(false)
          }
        },
        {
          threshold,
          rootMargin,
        }
      )

      observer.observe(element)

      return () => {
        observer.disconnect()
      }
    }, [threshold, rootMargin, once])

    const baseClass = React.useMemo(() => {
      switch (type) {
        case "fade":
          return "scroll-fade-in"
        case "slide-up":
          return "scroll-slide-up"
        case "slide-left":
          return "opacity-0 translate-x-4 transition-all duration-600"
        case "slide-right":
          return "opacity-0 -translate-x-4 transition-all duration-600"
        default:
          return "scroll-fade-in"
      }
    }, [type])

    return (
      <div
        ref={elementRef}
        className={cn(
          [
            baseClass,
            isVisible && "is-visible",
            isVisible && type === "slide-left" && "opacity-100 translate-x-0",
            isVisible && type === "slide-right" && "opacity-100 translate-x-0",
          ].join(" "),
          className
        )}
        style={{
          transitionDelay: stagger ? `${stagger}ms` : undefined,
        }}
        {...props}
      >
        {children}
      </div>
    )
  }
)

ScrollReveal.displayName = "ScrollReveal"

/* ============================================================================
   STAGGER CONTAINER
   ============================================================================ */

export interface StaggerContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Stagger delay between children (ms)
   */
  staggerDelay?: number
  /**
   * Animation type for children
   */
  animationType?: "fade" | "slide-up" | "scale"
  /**
   * Children to stagger
   */
  children: React.ReactNode
}

/**
 * StaggerContainer Component
 *
 * Animates children with staggered delay
 *
 * Usage:
 * ```tsx
 * <StaggerContainer staggerDelay={50}>
 *   <Card>Item 1</Card>
 *   <Card>Item 2</Card>
 *   <Card>Item 3</Card>
 * </StaggerContainer>
 * ```
 */
export const StaggerContainer = React.forwardRef<HTMLDivElement, StaggerContainerProps>(
  ({ className, staggerDelay = 50, animationType = "fade", children, ...props }, ref) => {
    const animationClass = React.useMemo(() => {
      switch (animationType) {
        case "fade":
          return "animate-fade-in"
        case "slide-up":
          return "animate-slide-up"
        case "scale":
          return "animate-scale-in"
        default:
          return "animate-fade-in"
      }
    }, [animationType])

    return (
      <div ref={ref} className={cn("", className)} {...props}>
        {React.Children.map(children, (child, index) => {
          if (!React.isValidElement(child)) return child

          return (
            <div
              className={animationClass}
              style={{
                animationDelay: `${index * staggerDelay}ms`,
              }}
            >
              {child}
            </div>
          )
        })}
      </div>
    )
  }
)

StaggerContainer.displayName = "StaggerContainer"

/* ============================================================================
   MODAL TRANSITION
   ============================================================================ */

export interface ModalTransitionProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Modal open state
   */
  open: boolean
  /**
   * Callback when animation completes
   */
  onAnimationEnd?: () => void
  /**
   * Children to animate
   */
  children: React.ReactNode
}

/**
 * ModalTransition Component
 *
 * Handles modal enter/exit animations
 *
 * Usage:
 * ```tsx
 * <ModalTransition open={isOpen}>
 *   <ModalContent />
 * </ModalTransition>
 * ```
 */
export const ModalTransition = React.forwardRef<HTMLDivElement, ModalTransitionProps>(
  ({ className, open, onAnimationEnd, children, ...props }, ref) => {
    const [shouldRender, setShouldRender] = React.useState(open)

    React.useEffect(() => {
      if (open) {
        setShouldRender(true)
      }
    }, [open])

    const handleAnimationEnd = () => {
      if (!open) {
        setShouldRender(false)
      }
      onAnimationEnd?.()
    }

    if (!shouldRender) return null

    return (
      <div
        ref={ref}
        className={cn(
          [
            "fixed inset-0 z-50",
            open ? "modal-backdrop-enter" : "modal-backdrop-exit",
          ].join(" "),
          className
        )}
        onAnimationEnd={handleAnimationEnd}
        {...props}
      >
        <div className={open ? "modal-content-enter" : "modal-content-exit"}>
          {children}
        </div>
      </div>
    )
  }
)

ModalTransition.displayName = "ModalTransition"

/* ============================================================================
   EXPORTS
   ============================================================================ */

export type {
  PageTransitionProps,
  ScrollRevealProps,
  StaggerContainerProps,
  ModalTransitionProps,
}
