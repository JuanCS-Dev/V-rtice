/**
 * ═══════════════════════════════════════════════════════════════════════════
 * SIDEBAR COMPONENT - CLAUDE.AI GREEN STYLE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * REESCRITO DO ZERO - NÃO é adaptação
 * Baseado em: Claude.ai chat sidebar
 * Estilo: Clean, collapsible, verde accents
 */

import * as React from "react";
import {
  ChevronLeft,
  ChevronRight,
  Home,
  Settings,
  HelpCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "./button";
import { Badge } from "./badge";
import "../../../styles/claude-design-green.css";

export interface SidebarProps extends React.HTMLAttributes<HTMLElement> {
  /**
   * Sidebar items
   */
  items?: SidebarItem[];
  /**
   * Collapsed state
   */
  collapsed?: boolean;
  /**
   * On collapse toggle
   */
  onCollapsedChange?: (collapsed: boolean) => void;
  /**
   * Show header
   */
  showHeader?: boolean;
  /**
   * Header content
   */
  header?: React.ReactNode;
  /**
   * Show footer
   */
  showFooter?: boolean;
  /**
   * Footer content
   */
  footer?: React.ReactNode;
  /**
   * Position
   */
  position?: "left" | "right";
  /**
   * Collapsible
   */
  collapsible?: boolean;
}

export interface SidebarItem {
  id?: string;
  label: string;
  icon?: React.ReactNode;
  href?: string;
  onClick?: () => void;
  badge?: string | number;
  badgeVariant?: "default" | "success" | "warning" | "destructive";
  active?: boolean;
  disabled?: boolean;
  children?: SidebarItem[];
}

/**
 * Sidebar Component - Claude.ai Green Style
 *
 * Clean collapsible sidebar with verde accents
 *
 * Usage:
 * ```tsx
 * <Sidebar
 *   items={[
 *     { label: 'Home', icon: <Home />, active: true },
 *     { label: 'Settings', icon: <Settings /> },
 *   ]}
 *   collapsed={collapsed}
 *   onCollapsedChange={setCollapsed}
 * />
 * ```
 */
export const Sidebar = React.forwardRef<HTMLElement, SidebarProps>(
  (
    {
      className,
      items = [],
      collapsed = false,
      onCollapsedChange,
      showHeader = true,
      header,
      showFooter = true,
      footer,
      position = "left",
      collapsible = true,
      children,
      ...props
    },
    ref,
  ) => {
    const [expandedItems, setExpandedItems] = React.useState<Set<string>>(
      new Set(),
    );

    const toggleExpanded = (id: string) => {
      const newExpanded = new Set(expandedItems);
      if (newExpanded.has(id)) {
        newExpanded.delete(id);
      } else {
        newExpanded.add(id);
      }
      setExpandedItems(newExpanded);
    };

    return (
      <aside
        ref={ref}
        className={cn(
          [
            // Layout
            "flex flex-col",
            "h-full",
            "border-[var(--sidebar-border)]",
            position === "left" ? "border-r" : "border-l",
            // Background - Claude.ai style
            "bg-[var(--sidebar-background)]",
            // Width
            collapsed ? "w-16" : "w-64",
            // Transition
            "transition-all duration-[var(--transition-normal)]",
            // Shadow
            "shadow-[var(--shadow-sm)]",
          ].join(" "),
          className,
        )}
        {...props}
      >
        {/* Header */}
        {showHeader && (
          <div
            className={cn(
              [
                "flex items-center",
                collapsed ? "justify-center" : "justify-between",
                "h-16 px-[var(--space-4)]",
                "border-b border-[var(--sidebar-border)]",
              ].join(" "),
            )}
          >
            {!collapsed &&
              (header || (
                <div
                  className="text-[var(--text-xl)] font-[var(--font-display)] font-bold"
                  style={{ color: "var(--sidebar-primary)" }}
                >
                  VÉRTICE 💚
                </div>
              ))}

            {collapsible && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onCollapsedChange?.(!collapsed)}
                aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
              >
                {collapsed ? (
                  <ChevronRight className="h-4 w-4" />
                ) : (
                  <ChevronLeft className="h-4 w-4" />
                )}
              </Button>
            )}
          </div>
        )}

        {/* Navigation Items */}
        <nav className="flex-1 overflow-y-auto py-[var(--space-4)]">
          <div className="space-y-[var(--space-1)] px-[var(--space-2)]">
            {items.map((item, index) => (
              <SidebarItemComponent
                key={item.id || index}
                item={item}
                collapsed={collapsed}
                expanded={expandedItems.has(item.id || `${index}`)}
                onToggleExpand={() => toggleExpanded(item.id || `${index}`)}
              />
            ))}
          </div>

          {/* Custom children */}
          {children}
        </nav>

        {/* Footer */}
        {showFooter && (
          <div
            className={cn(
              [
                "px-[var(--space-4)] py-[var(--space-4)]",
                "border-t border-[var(--sidebar-border)]",
              ].join(" "),
            )}
          >
            {footer || (
              <div className={cn(collapsed ? "flex justify-center" : "")}>
                <Button
                  variant="ghost"
                  size={collapsed ? "icon" : "default"}
                  className="w-full justify-start"
                >
                  <HelpCircle className="h-4 w-4" />
                  {!collapsed && <span className="ml-2">Help</span>}
                </Button>
              </div>
            )}
          </div>
        )}
      </aside>
    );
  },
);

Sidebar.displayName = "Sidebar";

/**
 * Sidebar Item Component
 */
function SidebarItemComponent({
  item,
  collapsed,
  expanded,
  onToggleExpand,
  level = 0,
}: {
  item: SidebarItem;
  collapsed: boolean;
  expanded: boolean;
  onToggleExpand: () => void;
  level?: number;
}) {
  const hasChildren = item.children && item.children.length > 0;
  const paddingLeft = collapsed ? 0 : level * 12;

  if (hasChildren) {
    return (
      <div>
        <button
          onClick={onToggleExpand}
          disabled={item.disabled}
          className={cn(
            [
              "w-full flex items-center gap-[var(--space-3)]",
              collapsed ? "justify-center" : "justify-between",
              "px-[var(--space-3)] py-[var(--space-2)]",
              "text-[var(--text-sm)]",
              "font-[var(--font-primary)]",
              "font-medium",
              "rounded-[var(--radius-md)]",
              "transition-all duration-[var(--transition-fast)]",
              // States
              item.active
                ? "bg-[var(--sidebar-accent)] text-[var(--sidebar-primary)] shadow-[var(--shadow-glow-green-soft)]"
                : "text-[var(--sidebar-foreground)] hover:bg-[var(--sidebar-accent)]",
              item.disabled && "opacity-50 cursor-not-allowed",
            ].join(" "),
          )}
          style={{ paddingLeft: `${paddingLeft}px` }}
        >
          <span className="flex items-center gap-[var(--space-3)]">
            {item.icon && <span className="flex-shrink-0">{item.icon}</span>}
            {!collapsed && <span>{item.label}</span>}
          </span>

          {!collapsed && (
            <span className="flex items-center gap-2">
              {item.badge && (
                <Badge
                  variant={item.badgeVariant || "default"}
                  className="text-xs"
                >
                  {item.badge}
                </Badge>
              )}
              <ChevronRight
                className={cn(
                  "h-4 w-4 transition-transform",
                  expanded && "rotate-90",
                )}
              />
            </span>
          )}
        </button>

        {/* Children */}
        {!collapsed && expanded && (
          <div className="mt-[var(--space-1)] space-y-[var(--space-1)]">
            {item.children?.map((child, index) => (
              <SidebarItemComponent
                key={child.id || index}
                item={child}
                collapsed={collapsed}
                expanded={false}
                onToggleExpand={() => {}}
                level={level + 1}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <a
      href={item.href}
      onClick={item.onClick}
      className={cn(
        [
          "flex items-center gap-[var(--space-3)]",
          collapsed ? "justify-center" : "",
          "px-[var(--space-3)] py-[var(--space-2)]",
          "text-[var(--text-sm)]",
          "font-[var(--font-primary)]",
          "font-medium",
          "rounded-[var(--radius-md)]",
          "transition-all duration-[var(--transition-fast)]",
          // States
          item.active
            ? "bg-[var(--sidebar-accent)] text-[var(--sidebar-primary)] shadow-[var(--shadow-glow-green-soft)]"
            : "text-[var(--sidebar-foreground)] hover:bg-[var(--sidebar-accent)]",
          item.disabled && "opacity-50 cursor-not-allowed pointer-events-none",
        ].join(" "),
      )}
      style={{ paddingLeft: `${paddingLeft}px` }}
      title={collapsed ? item.label : undefined}
    >
      {item.icon && <span className="flex-shrink-0">{item.icon}</span>}
      {!collapsed && (
        <>
          <span className="flex-1">{item.label}</span>
          {item.badge && (
            <Badge variant={item.badgeVariant || "default"} className="text-xs">
              {item.badge}
            </Badge>
          )}
        </>
      )}
    </a>
  );
}

export { SidebarItemComponent };
export type { SidebarItem };
