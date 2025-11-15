/**
 * ═══════════════════════════════════════════════════════════════════════════
 * CLAUDE.AI GREEN DESIGN SYSTEM - COMPONENT EXPORTS
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Componentes UI REESCRITOS DO ZERO no estilo Claude.ai com verde
 *
 * Usage:
 * ```tsx
 * import { Button, Input, Card, Badge } from '@/components/ui/claude'
 * ```
 */

// ============================================================================
// CORE COMPONENTS
// ============================================================================

// Button
export { Button, buttonVariants } from "./button";
export type { ButtonProps } from "./button";

// Input
export { Input } from "./input";
export type { InputProps } from "./input";

// Textarea
export { Textarea } from "./textarea";
export type { TextareaProps } from "./textarea";

// Label
export { Label } from "./label";

// Card
export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
} from "./card";

// Badge
export { Badge, badgeVariants } from "./badge";
export type { BadgeProps } from "./badge";

// ============================================================================
// FORM COMPONENTS
// ============================================================================

// Select
export {
  Select,
  SelectGroup,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectLabel,
  SelectItem,
  SelectSeparator,
  SelectScrollUpButton,
  SelectScrollDownButton,
} from "./select";

// Switch
export { Switch } from "./switch";

// Checkbox
export { Checkbox } from "./checkbox";

// ============================================================================
// FEEDBACK COMPONENTS
// ============================================================================

// Alert
export { Alert, AlertTitle, AlertDescription, alertVariants } from "./alert";
export type { AlertProps } from "./alert";

// Spinner
export { Spinner, LoadingOverlay, spinnerVariants } from "./spinner";
export type { SpinnerProps, LoadingOverlayProps } from "./spinner";

// Skeleton
export { Skeleton, CardSkeleton, ListSkeleton } from "./skeleton";

// ============================================================================
// LAYOUT COMPONENTS
// ============================================================================

// Navbar
export { Navbar, NavItemComponent, MobileNavItem } from "./navbar";
export type { NavbarProps, NavItem } from "./navbar";

// Sidebar
export { Sidebar, SidebarItemComponent } from "./sidebar";
export type { SidebarProps, SidebarItem } from "./sidebar";

// Container & Grid
export { Container, Grid, Stack, Inline, Section } from "./container";
export { containerVariants, gridVariants } from "./container";
export type {
  ContainerProps,
  GridProps,
  StackProps,
  InlineProps,
  SectionProps,
} from "./container";

// ============================================================================
// WIDGET COMPONENTS
// ============================================================================

// Stat Cards
export { StatCard, MetricCard } from "./stat-card";
export type { StatCardProps, MetricCardProps } from "./stat-card";

// Data Table
export { DataTable } from "./data-table";
export type { DataTableProps, Column } from "./data-table";

// Chart Config
export {
  chartColors,
  chartTheme,
  defaultChartProps,
  lineChartConfig,
  barChartConfig,
  areaChartConfig,
  pieChartConfig,
  getGradientId,
  getChartColor,
  ChartContainer,
} from "./chart-config";

// ============================================================================
// ANIMATIONS & TRANSITIONS
// ============================================================================

// Page Transitions
export {
  PageTransition,
  ScrollReveal,
  StaggerContainer,
  ModalTransition,
} from "./page-transition";
export type {
  PageTransitionProps,
  ScrollRevealProps,
  StaggerContainerProps,
  ModalTransitionProps,
} from "./page-transition";

// Advanced Loading
export {
  ProgressBar,
  CircularProgress,
  PulseLoader,
  TypingIndicator,
  SkeletonPulse,
  LoadingDots,
  RippleLoader,
} from "./advanced-loading";
export type {
  ProgressBarProps,
  CircularProgressProps,
  PulseLoaderProps,
  TypingIndicatorProps,
  SkeletonPulseProps,
  LoadingDotsProps,
  RippleLoaderProps,
} from "./advanced-loading";

// Animation Hooks
export {
  useInView,
  useScrollReveal,
  useStaggerAnimation,
  useHoverAnimation,
  useGesture,
  useReducedMotion,
  useAnimationFrame,
} from "./use-animations";
export type {
  UseInViewOptions,
  UseScrollRevealOptions,
  ScrollRevealResult,
  UseStaggerAnimationOptions,
  UseHoverAnimationResult,
  GestureState,
  UseGestureOptions,
} from "./use-animations";

/**
 * Design System Tokens
 *
 * CRITICAL: Certifique-se de importar o CSS do design system:
 * @import '../../../styles/claude-design-green.css'
 * @import '../../../styles/claude-animations.css'
 *
 * Total Components: 35+
 *
 * CORE (12):
 * - Button, Input, Textarea, Label
 * - Card (+ 5 subcomponents)
 * - Badge
 * - Select (+ 7 subcomponents)
 * - Switch, Checkbox
 * - Alert (+ 2 subcomponents)
 * - Spinner, LoadingOverlay
 * - Skeleton, CardSkeleton, ListSkeleton
 *
 * LAYOUT (9+):
 * - Navbar (+ 2 subcomponents)
 * - Sidebar (+ 1 subcomponent)
 * - Container, Grid, Stack, Inline, Section
 *
 * WIDGETS (3+):
 * - StatCard, MetricCard
 * - DataTable
 * - Chart Config (verde theme)
 *
 * ANIMATIONS (11+):
 * - PageTransition, ScrollReveal, StaggerContainer, ModalTransition
 * - ProgressBar, CircularProgress, PulseLoader, TypingIndicator
 * - SkeletonPulse, LoadingDots, RippleLoader
 *
 * HOOKS (7):
 * - useInView, useScrollReveal, useStaggerAnimation
 * - useHoverAnimation, useGesture, useReducedMotion, useAnimationFrame
 */
