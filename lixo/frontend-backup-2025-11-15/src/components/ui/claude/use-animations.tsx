/**
 * ═══════════════════════════════════════════════════════════════════════════
 * ANIMATION HOOKS - CLAUDE.AI GREEN STYLE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * React hooks para animações e micro-interactions
 *
 * Hooks:
 * - useScrollReveal: Reveal elements on scroll
 * - useInView: Detect if element is in viewport
 * - useStaggerAnimation: Stagger children animations
 * - useHoverAnimation: Hover state management
 * - useGesture: Touch/mouse gesture detection
 */

import * as React from "react"

/* ============================================================================
   USE IN VIEW
   ============================================================================ */

export interface UseInViewOptions {
  /**
   * Threshold for IntersectionObserver (0-1)
   */
  threshold?: number | number[]
  /**
   * Root margin
   */
  rootMargin?: string
  /**
   * Trigger once or every time
   */
  triggerOnce?: boolean
  /**
   * Root element
   */
  root?: Element | null
}

/**
 * useInView Hook
 *
 * Detects when element enters/exits viewport
 *
 * Usage:
 * ```tsx
 * const [ref, isInView] = useInView({ threshold: 0.5 })
 * return <div ref={ref}>{isInView ? 'Visible!' : 'Not visible'}</div>
 * ```
 */
export function useInView<T extends Element = HTMLDivElement>(
  options: UseInViewOptions = {}
): [React.RefObject<T>, boolean] {
  const {
    threshold = 0,
    rootMargin = "0px",
    triggerOnce = false,
    root = null,
  } = options

  const ref = React.useRef<T>(null)
  const [isInView, setIsInView] = React.useState(false)

  React.useEffect(() => {
    const element = ref.current
    if (!element) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        const inView = entry.isIntersecting
        setIsInView(inView)

        if (inView && triggerOnce) {
          observer.unobserve(element)
        }
      },
      {
        threshold,
        rootMargin,
        root,
      }
    )

    observer.observe(element)

    return () => {
      observer.disconnect()
    }
  }, [threshold, rootMargin, triggerOnce, root])

  return [ref, isInView]
}

/* ============================================================================
   USE SCROLL REVEAL
   ============================================================================ */

export interface UseScrollRevealOptions extends UseInViewOptions {
  /**
   * Animation delay (ms)
   */
  delay?: number
  /**
   * Animation duration (ms)
   */
  duration?: number
}

export interface ScrollRevealResult {
  /**
   * Ref to attach to element
   */
  ref: React.RefObject<HTMLDivElement>
  /**
   * Is element in view
   */
  isInView: boolean
  /**
   * CSS class to apply
   */
  className: string
  /**
   * Inline styles
   */
  style: React.CSSProperties
}

/**
 * useScrollReveal Hook
 *
 * Complete scroll reveal with animation classes
 *
 * Usage:
 * ```tsx
 * const reveal = useScrollReveal({ delay: 100 })
 * return <div ref={reveal.ref} className={reveal.className} style={reveal.style}>...</div>
 * ```
 */
export function useScrollReveal(
  options: UseScrollRevealOptions = {}
): ScrollRevealResult {
  const { delay = 0, duration = 600, ...inViewOptions } = options
  const [ref, isInView] = useInView(inViewOptions)

  return {
    ref,
    isInView,
    className: isInView ? "is-visible" : "",
    style: {
      transitionDelay: `${delay}ms`,
      transitionDuration: `${duration}ms`,
    },
  }
}

/* ============================================================================
   USE STAGGER ANIMATION
   ============================================================================ */

export interface UseStaggerAnimationOptions {
  /**
   * Delay between items (ms)
   */
  staggerDelay?: number
  /**
   * Base delay before first item (ms)
   */
  baseDelay?: number
  /**
   * Animation duration (ms)
   */
  duration?: number
}

/**
 * useStaggerAnimation Hook
 *
 * Generates stagger delays for list items
 *
 * Usage:
 * ```tsx
 * const getStaggerStyle = useStaggerAnimation({ staggerDelay: 50 })
 * return items.map((item, i) => (
 *   <div key={i} style={getStaggerStyle(i)}>...</div>
 * ))
 * ```
 */
export function useStaggerAnimation(options: UseStaggerAnimationOptions = {}) {
  const { staggerDelay = 50, baseDelay = 0, duration = 400 } = options

  return React.useCallback(
    (index: number): React.CSSProperties => ({
      animationDelay: `${baseDelay + index * staggerDelay}ms`,
      animationDuration: `${duration}ms`,
    }),
    [staggerDelay, baseDelay, duration]
  )
}

/* ============================================================================
   USE HOVER ANIMATION
   ============================================================================ */

export interface UseHoverAnimationResult {
  /**
   * Is element hovered
   */
  isHovered: boolean
  /**
   * Props to spread on element
   */
  hoverProps: {
    onMouseEnter: () => void
    onMouseLeave: () => void
  }
}

/**
 * useHoverAnimation Hook
 *
 * Track hover state for animations
 *
 * Usage:
 * ```tsx
 * const { isHovered, hoverProps } = useHoverAnimation()
 * return <div {...hoverProps}>{isHovered ? '👋' : '👍'}</div>
 * ```
 */
export function useHoverAnimation(): UseHoverAnimationResult {
  const [isHovered, setIsHovered] = React.useState(false)

  const hoverProps = React.useMemo(
    () => ({
      onMouseEnter: () => setIsHovered(true),
      onMouseLeave: () => setIsHovered(false),
    }),
    []
  )

  return { isHovered, hoverProps }
}

/* ============================================================================
   USE GESTURE
   ============================================================================ */

export interface GestureState {
  /**
   * Is dragging/panning
   */
  isDragging: boolean
  /**
   * Current delta from start
   */
  delta: { x: number; y: number }
  /**
   * Velocity
   */
  velocity: { x: number; y: number }
  /**
   * Start position
   */
  start: { x: number; y: number }
  /**
   * Current position
   */
  current: { x: number; y: number }
}

export interface UseGestureOptions {
  /**
   * Minimum distance to activate (px)
   */
  threshold?: number
  /**
   * On drag start
   */
  onDragStart?: (state: GestureState) => void
  /**
   * On drag
   */
  onDrag?: (state: GestureState) => void
  /**
   * On drag end
   */
  onDragEnd?: (state: GestureState) => void
}

/**
 * useGesture Hook
 *
 * Handle touch/mouse gestures
 *
 * Usage:
 * ```tsx
 * const gestureProps = useGesture({
 *   onDrag: (state) => console.log('dragging', state.delta)
 * })
 * return <div {...gestureProps}>Drag me</div>
 * ```
 */
export function useGesture(options: UseGestureOptions = {}) {
  const { threshold = 5, onDragStart, onDrag, onDragEnd } = options

  const [state, setState] = React.useState<GestureState>({
    isDragging: false,
    delta: { x: 0, y: 0 },
    velocity: { x: 0, y: 0 },
    start: { x: 0, y: 0 },
    current: { x: 0, y: 0 },
  })

  const startTimeRef = React.useRef<number>(0)
  const lastPosRef = React.useRef({ x: 0, y: 0 })
  const lastTimeRef = React.useRef<number>(0)

  const handleStart = React.useCallback(
    (clientX: number, clientY: number) => {
      const newState: GestureState = {
        isDragging: false,
        delta: { x: 0, y: 0 },
        velocity: { x: 0, y: 0 },
        start: { x: clientX, y: clientY },
        current: { x: clientX, y: clientY },
      }

      setState(newState)
      startTimeRef.current = Date.now()
      lastPosRef.current = { x: clientX, y: clientY }
      lastTimeRef.current = Date.now()
    },
    []
  )

  const handleMove = React.useCallback(
    (clientX: number, clientY: number) => {
      setState((prev) => {
        const delta = {
          x: clientX - prev.start.x,
          y: clientY - prev.start.y,
        }

        // Check if exceeded threshold
        const distance = Math.sqrt(delta.x ** 2 + delta.y ** 2)
        const isDragging = prev.isDragging || distance > threshold

        // Calculate velocity
        const now = Date.now()
        const dt = now - lastTimeRef.current
        const velocity = {
          x: dt > 0 ? (clientX - lastPosRef.current.x) / dt : 0,
          y: dt > 0 ? (clientY - lastPosRef.current.y) / dt : 0,
        }

        lastPosRef.current = { x: clientX, y: clientY }
        lastTimeRef.current = now

        const newState: GestureState = {
          isDragging,
          delta,
          velocity,
          start: prev.start,
          current: { x: clientX, y: clientY },
        }

        // Trigger callbacks
        if (isDragging && !prev.isDragging) {
          onDragStart?.(newState)
        } else if (isDragging) {
          onDrag?.(newState)
        }

        return newState
      })
    },
    [threshold, onDragStart, onDrag]
  )

  const handleEnd = React.useCallback(() => {
    setState((prev) => {
      if (prev.isDragging) {
        onDragEnd?.(prev)
      }

      return {
        ...prev,
        isDragging: false,
      }
    })
  }, [onDragEnd])

  // Mouse handlers
  const handleMouseDown = React.useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault()
      handleStart(e.clientX, e.clientY)
    },
    [handleStart]
  )

  const handleMouseMove = React.useCallback(
    (e: MouseEvent) => {
      if (state.start.x !== 0 || state.start.y !== 0) {
        handleMove(e.clientX, e.clientY)
      }
    },
    [state.start, handleMove]
  )

  const handleMouseUp = React.useCallback(() => {
    handleEnd()
  }, [handleEnd])

  // Touch handlers
  const handleTouchStart = React.useCallback(
    (e: React.TouchEvent) => {
      const touch = e.touches[0]
      handleStart(touch.clientX, touch.clientY)
    },
    [handleStart]
  )

  const handleTouchMove = React.useCallback(
    (e: TouchEvent) => {
      if (e.touches.length > 0) {
        const touch = e.touches[0]
        handleMove(touch.clientX, touch.clientY)
      }
    },
    [handleMove]
  )

  const handleTouchEnd = React.useCallback(() => {
    handleEnd()
  }, [handleEnd])

  // Add/remove event listeners
  React.useEffect(() => {
    if (state.start.x !== 0 || state.start.y !== 0) {
      window.addEventListener("mousemove", handleMouseMove)
      window.addEventListener("mouseup", handleMouseUp)
      window.addEventListener("touchmove", handleTouchMove)
      window.addEventListener("touchend", handleTouchEnd)

      return () => {
        window.removeEventListener("mousemove", handleMouseMove)
        window.removeEventListener("mouseup", handleMouseUp)
        window.removeEventListener("touchmove", handleTouchMove)
        window.removeEventListener("touchend", handleTouchEnd)
      }
    }
  }, [state.start, handleMouseMove, handleMouseUp, handleTouchMove, handleTouchEnd])

  return {
    onMouseDown: handleMouseDown,
    onTouchStart: handleTouchStart,
    gestureState: state,
  }
}

/* ============================================================================
   USE REDUCED MOTION
   ============================================================================ */

/**
 * useReducedMotion Hook
 *
 * Detect user's motion preference
 *
 * Usage:
 * ```tsx
 * const prefersReducedMotion = useReducedMotion()
 * return <div className={prefersReducedMotion ? '' : 'animate-fade-in'}>...</div>
 * ```
 */
export function useReducedMotion(): boolean {
  const [prefersReducedMotion, setPrefersReducedMotion] = React.useState(false)

  React.useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)")
    setPrefersReducedMotion(mediaQuery.matches)

    const handleChange = (event: MediaQueryListEvent) => {
      setPrefersReducedMotion(event.matches)
    }

    mediaQuery.addEventListener("change", handleChange)

    return () => {
      mediaQuery.removeEventListener("change", handleChange)
    }
  }, [])

  return prefersReducedMotion
}

/* ============================================================================
   USE ANIMATION FRAME
   ============================================================================ */

/**
 * useAnimationFrame Hook
 *
 * Run callback on every animation frame
 *
 * Usage:
 * ```tsx
 * useAnimationFrame((deltaTime) => {
 *   // Update animation state
 * })
 * ```
 */
export function useAnimationFrame(callback: (deltaTime: number) => void) {
  const requestRef = React.useRef<number>()
  const previousTimeRef = React.useRef<number>()

  const animate = React.useCallback(
    (time: number) => {
      if (previousTimeRef.current !== undefined) {
        const deltaTime = time - previousTimeRef.current
        callback(deltaTime)
      }
      previousTimeRef.current = time
      requestRef.current = requestAnimationFrame(animate)
    },
    [callback]
  )

  React.useEffect(() => {
    requestRef.current = requestAnimationFrame(animate)
    return () => {
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current)
      }
    }
  }, [animate])
}

/* ============================================================================
   EXPORTS
   ============================================================================ */

export type {
  UseInViewOptions,
  UseScrollRevealOptions,
  ScrollRevealResult,
  UseStaggerAnimationOptions,
  UseHoverAnimationResult,
  GestureState,
  UseGestureOptions,
}
