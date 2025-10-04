/**
 * Widget Library - Shared Reusable Components
 *
 * Centralized export for all shared widgets used across dashboards.
 * Promotes consistency and reduces code duplication.
 *
 * Available Widgets:
 * - MetricCard: Displays metric label + value with variants
 * - ModuleStatusCard: Shows module status with online/offline indicators
 * - ActivityItem: Activity log item with severity-based styling
 * - PanelCard: Generic panel container with title and actions
 */

export { MetricCard } from './MetricCard';
export { ModuleStatusCard } from './ModuleStatusCard';
export { ActivityItem } from './ActivityItem';
export { PanelCard } from './PanelCard';

// Re-export for convenience
export default {
  MetricCard,
  ModuleStatusCard,
  ActivityItem,
  PanelCard
};
