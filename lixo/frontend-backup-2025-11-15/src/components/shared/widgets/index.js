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

import { MetricCard } from "./MetricCard";
import { ModuleStatusCard } from "./ModuleStatusCard";
import { ActivityItem } from "./ActivityItem";
import { PanelCard } from "./PanelCard";

export { MetricCard, ModuleStatusCard, ActivityItem, PanelCard };

export default {
  MetricCard,
  ModuleStatusCard,
  ActivityItem,
  PanelCard,
};
