/**
 * ═══════════════════════════════════════════════════════════════════════════
 * ADVANCED LOADING STATES - CLAUDE.AI GREEN STYLE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Loading components com VERDE accent (#10b981)
 * Baseado em: Claude.ai subtle, calm loading states
 *
 * Components:
 * - ProgressBar: Linear progress com verde
 * - CircularProgress: Circular spinner verde
 * - PulseLoader: Pulsing dots verde
 * - TypingIndicator: Chat typing dots verde
 * - SkeletonPulse: Animated skeleton verde accent
 */

import * as React from "react";
import { cn } from "@/lib/utils";
import "../../../styles/claude-animations.css";

/* ============================================================================
   PROGRESS BAR
   ============================================================================ */

export interface ProgressBarProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Progress value (0-100)
   */
  value?: number;
  /**
   * Indeterminate mode (no value)
   */
  indeterminate?: boolean;
  /**
   * Bar size
   */
  size?: "sm" | "md" | "lg";
  /**
   * Show percentage label
   */
  showLabel?: boolean;
}

/**
 * ProgressBar Component
 *
 * Linear progress indicator com verde
 *
 * Usage:
 * ```tsx
 * <ProgressBar value={75} showLabel />
 * <ProgressBar indeterminate />
 * ```
 */
export const ProgressBar = React.forwardRef<HTMLDivElement, ProgressBarProps>(
  (
    {
      className,
      value = 0,
      indeterminate = false,
      size = "md",
      showLabel = false,
      ...props
    },
    ref,
  ) => {
    const height = {
      sm: "h-1",
      md: "h-2",
      lg: "h-3",
    }[size];

    if (indeterminate) {
      return (
        <div ref={ref} className={cn("w-full", className)} {...props}>
          <div className={cn("progress-indeterminate w-full", height)} />
        </div>
      );
    }

    const clampedValue = Math.min(Math.max(value, 0), 100);

    return (
      <div ref={ref} className={cn("w-full", className)} {...props}>
        <div
          className={cn(
            [
              "relative w-full overflow-hidden rounded-full",
              "bg-[var(--muted)]",
              height,
            ].join(" "),
          )}
        >
          <div
            className={cn(
              [
                "h-full rounded-full",
                "bg-[var(--primary)]",
                "transition-all duration-500 ease-smooth",
              ].join(" "),
            )}
            style={{ width: `${clampedValue}%` }}
          />
        </div>
        {showLabel && (
          <div className="mt-1 text-center text-[var(--text-xs)] text-[var(--muted-foreground)]">
            {Math.round(clampedValue)}%
          </div>
        )}
      </div>
    );
  },
);

ProgressBar.displayName = "ProgressBar";

/* ============================================================================
   CIRCULAR PROGRESS
   ============================================================================ */

export interface CircularProgressProps
  extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Progress value (0-100)
   */
  value?: number;
  /**
   * Indeterminate mode (spinner)
   */
  indeterminate?: boolean;
  /**
   * Size in pixels
   */
  size?: number;
  /**
   * Stroke width
   */
  strokeWidth?: number;
  /**
   * Show percentage in center
   */
  showLabel?: boolean;
}

/**
 * CircularProgress Component
 *
 * Circular progress/spinner com verde
 *
 * Usage:
 * ```tsx
 * <CircularProgress value={60} showLabel />
 * <CircularProgress indeterminate />
 * ```
 */
export const CircularProgress = React.forwardRef<
  HTMLDivElement,
  CircularProgressProps
>(
  (
    {
      className,
      value = 0,
      indeterminate = false,
      size = 40,
      strokeWidth = 3,
      showLabel = false,
      ...props
    },
    ref,
  ) => {
    const clampedValue = Math.min(Math.max(value, 0), 100);
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (clampedValue / 100) * circumference;

    return (
      <div
        ref={ref}
        className={cn("inline-flex items-center justify-center", className)}
        style={{ width: size, height: size }}
        {...props}
      >
        <svg
          className={indeterminate ? "animate-spin" : ""}
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
        >
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="var(--muted)"
            strokeWidth={strokeWidth}
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="var(--primary)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={indeterminate ? circumference * 0.75 : offset}
            style={{
              transition: indeterminate
                ? "none"
                : "stroke-dashoffset 500ms ease-smooth",
              transform: "rotate(-90deg)",
              transformOrigin: "center",
            }}
          />
        </svg>
        {showLabel && !indeterminate && (
          <div
            className="absolute text-[var(--text-xs)] font-medium text-[var(--foreground)]"
            style={{ fontSize: size / 4 }}
          >
            {Math.round(clampedValue)}%
          </div>
        )}
      </div>
    );
  },
);

CircularProgress.displayName = "CircularProgress";

/* ============================================================================
   PULSE LOADER
   ============================================================================ */

export interface PulseLoaderProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Number of dots
   */
  dots?: number;
  /**
   * Dot size
   */
  size?: "sm" | "md" | "lg";
  /**
   * Dot color (default: primary verde)
   */
  color?: string;
}

/**
 * PulseLoader Component
 *
 * Pulsing dots loader com verde
 *
 * Usage:
 * ```tsx
 * <PulseLoader />
 * <PulseLoader dots={5} size="lg" />
 * ```
 */
export const PulseLoader = React.forwardRef<HTMLDivElement, PulseLoaderProps>(
  ({ className, dots = 3, size = "md", color, ...props }, ref) => {
    const dotSize = {
      sm: "w-1.5 h-1.5",
      md: "w-2 h-2",
      lg: "w-3 h-3",
    }[size];

    return (
      <div
        ref={ref}
        className={cn("inline-flex items-center gap-1.5", className)}
        {...props}
      >
        {Array.from({ length: dots }).map((_, index) => (
          <div
            key={index}
            className={cn(
              [
                dotSize,
                "rounded-full",
                "animate-pulse",
                "bg-[var(--primary)]",
              ].join(" "),
            )}
            style={{
              animationDelay: `${index * 150}ms`,
              backgroundColor: color || undefined,
            }}
          />
        ))}
      </div>
    );
  },
);

PulseLoader.displayName = "PulseLoader";

/* ============================================================================
   TYPING INDICATOR
   ============================================================================ */

export interface TypingIndicatorProps
  extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Size of dots
   */
  size?: "sm" | "md" | "lg";
  /**
   * Label text
   */
  label?: string;
}

/**
 * TypingIndicator Component
 *
 * Chat-style typing indicator com verde bouncing dots
 *
 * Usage:
 * ```tsx
 * <TypingIndicator />
 * <TypingIndicator label="Claude is typing..." />
 * ```
 */
export const TypingIndicator = React.forwardRef<
  HTMLDivElement,
  TypingIndicatorProps
>(({ className, size = "md", label, ...props }, ref) => {
  const dotSize = {
    sm: "w-1 h-1",
    md: "w-1.5 h-1.5",
    lg: "w-2 h-2",
  }[size];

  return (
    <div
      ref={ref}
      className={cn("inline-flex items-center gap-2", className)}
      {...props}
    >
      <div className="typing-indicator">
        <span className={dotSize} />
        <span className={dotSize} />
        <span className={dotSize} />
      </div>
      {label && (
        <span className="text-[var(--text-sm)] text-[var(--muted-foreground)]">
          {label}
        </span>
      )}
    </div>
  );
});

TypingIndicator.displayName = "TypingIndicator";

/* ============================================================================
   SKELETON PULSE
   ============================================================================ */

export interface SkeletonPulseProps
  extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Use shimmer effect instead of pulse
   */
  shimmer?: boolean;
  /**
   * Width
   */
  width?: string | number;
  /**
   * Height
   */
  height?: string | number;
  /**
   * Border radius
   */
  rounded?: "none" | "sm" | "md" | "lg" | "full";
}

/**
 * SkeletonPulse Component
 *
 * Animated skeleton with verde accent
 *
 * Usage:
 * ```tsx
 * <SkeletonPulse className="h-4 w-[200px]" />
 * <SkeletonPulse shimmer width={300} height={20} rounded="md" />
 * ```
 */
export const SkeletonPulse = React.forwardRef<
  HTMLDivElement,
  SkeletonPulseProps
>(
  (
    {
      className,
      shimmer = false,
      width,
      height,
      rounded = "md",
      style,
      ...props
    },
    ref,
  ) => {
    const roundedClass = {
      none: "rounded-none",
      sm: "rounded-sm",
      md: "rounded-md",
      lg: "rounded-lg",
      full: "rounded-full",
    }[rounded];

    return (
      <div
        ref={ref}
        className={cn(
          [
            roundedClass,
            shimmer ? "skeleton-shimmer" : "animate-pulse bg-[var(--muted)]",
          ].join(" "),
          className,
        )}
        style={{
          width: typeof width === "number" ? `${width}px` : width,
          height: typeof height === "number" ? `${height}px` : height,
          ...style,
        }}
        {...props}
      />
    );
  },
);

SkeletonPulse.displayName = "SkeletonPulse";

/* ============================================================================
   LOADING DOTS
   ============================================================================ */

export interface LoadingDotsProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Dot size
   */
  size?: "sm" | "md" | "lg";
  /**
   * Text to show after dots
   */
  text?: string;
}

/**
 * LoadingDots Component
 *
 * Animated "..." loader
 *
 * Usage:
 * ```tsx
 * <LoadingDots text="Loading" />
 * ```
 */
export const LoadingDots = React.forwardRef<HTMLDivElement, LoadingDotsProps>(
  ({ className, size = "md", text = "Loading", ...props }, ref) => {
    const [dots, setDots] = React.useState("");

    React.useEffect(() => {
      const interval = setInterval(() => {
        setDots((prev) => (prev.length >= 3 ? "" : prev + "."));
      }, 500);

      return () => clearInterval(interval);
    }, []);

    const fontSize = {
      sm: "text-sm",
      md: "text-base",
      lg: "text-lg",
    }[size];

    return (
      <div
        ref={ref}
        className={cn(
          [
            "inline-flex items-center",
            fontSize,
            "text-[var(--muted-foreground)]",
          ].join(" "),
          className,
        )}
        {...props}
      >
        <span>{text}</span>
        <span className="inline-block w-8 text-left">{dots}</span>
      </div>
    );
  },
);

LoadingDots.displayName = "LoadingDots";

/* ============================================================================
   RIPPLE LOADER
   ============================================================================ */

export interface RippleLoaderProps
  extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Size of ripple
   */
  size?: number;
  /**
   * Ripple color (default: primary verde)
   */
  color?: string;
}

/**
 * RippleLoader Component
 *
 * Expanding ripple effect loader
 *
 * Usage:
 * ```tsx
 * <RippleLoader />
 * <RippleLoader size={60} />
 * ```
 */
export const RippleLoader = React.forwardRef<HTMLDivElement, RippleLoaderProps>(
  ({ className, size = 40, color, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "relative inline-flex items-center justify-center",
          className,
        )}
        style={{ width: size, height: size }}
        {...props}
      >
        {[0, 1].map((index) => (
          <div
            key={index}
            className="absolute rounded-full border-2 animate-pulse-green"
            style={{
              width: size,
              height: size,
              borderColor: color || "var(--primary)",
              animationDelay: index === 0 ? "0s" : "1s",
            }}
          />
        ))}
      </div>
    );
  },
);

RippleLoader.displayName = "RippleLoader";

/* ============================================================================
   EXPORTS
   ============================================================================ */

export type {
  ProgressBarProps,
  CircularProgressProps,
  PulseLoaderProps,
  TypingIndicatorProps,
  SkeletonPulseProps,
  LoadingDotsProps,
  RippleLoaderProps,
};
