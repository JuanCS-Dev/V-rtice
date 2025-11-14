/**
 * ═══════════════════════════════════════════════════════════════════════════
 * CHART CONFIGURATION - CLAUDE.AI GREEN STYLE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Configuração Recharts com paleta VERDE
 * NÃO laranja/vermelho!
 */

import "../../../styles/claude-design-green.css"

/**
 * Chart Color Palette - VERDE Theme
 *
 * CRITICAL: VERDE (#10b981), não laranja!
 */
export const chartColors = {
  // Primary - VERDE
  primary: "oklch(0.62 0.14 155.00)", // #10b981
  primaryLight: "oklch(0.72 0.15 150.00)",
  primaryDark: "oklch(0.56 0.13 155.00)",

  // Secondary colors
  purple: "oklch(0.69 0.16 290.41)",
  blue: "oklch(0.62 0.18 245.00)",
  cyan: "oklch(0.75 0.14 195.00)",
  pink: "oklch(0.88 0.04 298.18)",

  // Semantic
  success: "#10b981", // Verde (mesmo primary)
  warning: "#f59e0b", // Amber
  danger: "#ef4444",  // Red
  info: "#3b82f6",    // Blue

  // Gradients
  gradientPrimary: ["#10b981", "#059669"],
  gradientSecondary: ["#34d399", "#10b981"],
}

/**
 * Chart Theme Configuration for Recharts
 */
export const chartTheme = {
  // Text
  textColor: "var(--foreground)",
  textSecondary: "var(--muted-foreground)",
  fontSize: "var(--text-sm)",
  fontFamily: "var(--font-primary)",

  // Grid
  gridColor: "var(--border)",
  gridOpacity: 0.5,

  // Tooltip
  tooltip: {
    backgroundColor: "var(--popover)",
    borderColor: "var(--border)",
    borderRadius: "var(--radius-default)",
    padding: "var(--space-3)",
    textColor: "var(--popover-foreground)",
    shadow: "var(--shadow-md)",
  },

  // Legend
  legend: {
    textColor: "var(--foreground)",
    fontSize: "var(--text-sm)",
  },
}

/**
 * Default Recharts Props - VERDE Theme
 */
export const defaultChartProps = {
  // Margin
  margin: { top: 10, right: 10, left: 0, bottom: 0 },

  // Axis styling
  axisStyle: {
    stroke: "var(--border)",
    fontSize: "var(--text-sm)",
    fontFamily: "var(--font-primary)",
  },

  // Grid styling
  gridStyle: {
    stroke: "var(--border)",
    strokeDasharray: "3 3",
    opacity: 0.3,
  },

  // Tooltip styling
  tooltipStyle: {
    backgroundColor: "var(--popover)",
    border: "1px solid var(--border)",
    borderRadius: "var(--radius-default)",
    padding: "var(--space-3)",
    fontSize: "var(--text-sm)",
    fontFamily: "var(--font-primary)",
    color: "var(--popover-foreground)",
    boxShadow: "var(--shadow-md)",
  },
}

/**
 * Line Chart Config - VERDE
 */
export const lineChartConfig = {
  strokeWidth: 2,
  dot: {
    fill: chartColors.primary,
    r: 4,
    strokeWidth: 2,
    stroke: "var(--background)",
  },
  activeDot: {
    r: 6,
    strokeWidth: 2,
    stroke: "var(--background)",
  },
  stroke: chartColors.primary,
}

/**
 * Bar Chart Config - VERDE
 */
export const barChartConfig = {
  fill: chartColors.primary,
  radius: [4, 4, 0, 0] as [number, number, number, number],
  maxBarSize: 50,
}

/**
 * Area Chart Config - VERDE
 */
export const areaChartConfig = {
  stroke: chartColors.primary,
  fill: chartColors.primary,
  fillOpacity: 0.2,
  strokeWidth: 2,
}

/**
 * Pie Chart Config - Multiple colors with VERDE primary
 */
export const pieChartConfig = {
  colors: [
    chartColors.primary,      // Verde
    chartColors.purple,       // Purple
    chartColors.blue,         // Blue
    chartColors.cyan,         // Cyan
    chartColors.warning,      // Amber
    chartColors.info,         // Blue
  ],
  innerRadius: 60,
  outerRadius: 80,
  paddingAngle: 2,
}

/**
 * Helper: Apply verde gradient to chart
 */
export function getGradientId(id: string) {
  return `gradient-${id}`
}

/**
 * Helper: Get color by index (for multi-series charts)
 */
export function getChartColor(index: number): string {
  const colors = [
    chartColors.primary,
    chartColors.purple,
    chartColors.blue,
    chartColors.cyan,
    chartColors.pink,
  ]
  return colors[index % colors.length]
}

/**
 * Chart Container Wrapper
 */
export const ChartContainer: React.FC<{
  children: React.ReactNode
  className?: string
  title?: string
  description?: string
}> = ({ children, className, title, description }) => {
  return (
    <div
      className={`bg-[var(--card)] border border-[var(--border)] rounded-[var(--radius-default)] p-[var(--space-6)] shadow-[var(--shadow-sm)] ${className || ""}`}
    >
      {(title || description) && (
        <div className="mb-[var(--space-4)]">
          {title && (
            <h3 className="text-[var(--text-lg)] font-[var(--font-display)] font-semibold text-[var(--foreground)]">
              {title}
            </h3>
          )}
          {description && (
            <p className="text-[var(--text-sm)] font-[var(--font-primary)] text-[var(--muted-foreground)] mt-1">
              {description}
            </p>
          )}
        </div>
      )}
      {children}
    </div>
  )
}

/**
 * Export all
 */
export default {
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
}
