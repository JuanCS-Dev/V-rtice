/**
 * ═══════════════════════════════════════════════════════════════════════════
 * DATA TABLE COMPONENT - CLAUDE.AI GREEN STYLE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * REESCRITO DO ZERO - NÃO é adaptação
 * Baseado em: Claude.ai tables
 * Estilo: Clean, sortable, verde accents
 */

import * as React from "react";
import { ChevronDown, ChevronUp, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "./badge";
import "../../../styles/claude-design-green.css";

export interface Column<T = any> {
  key: string;
  title: string;
  sortable?: boolean;
  render?: (value: any, row: T, index: number) => React.ReactNode;
  width?: string;
  align?: "left" | "center" | "right";
}

export interface DataTableProps<T = any>
  extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Table columns
   */
  columns: Column<T>[];
  /**
   * Table data
   */
  data: T[];
  /**
   * Loading state
   */
  loading?: boolean;
  /**
   * Empty message
   */
  emptyMessage?: string;
  /**
   * On row click
   */
  onRowClick?: (row: T, index: number) => void;
  /**
   * Sortable
   */
  sortable?: boolean;
  /**
   * Hoverable rows
   */
  hoverable?: boolean;
  /**
   * Striped rows
   */
  striped?: boolean;
  /**
   * Compact spacing
   */
  compact?: boolean;
}

/**
 * DataTable Component - Claude.ai Green Style
 *
 * Clean sortable table with verde accents
 *
 * Usage:
 * ```tsx
 * <DataTable
 *   columns={[
 *     { key: 'name', title: 'Name', sortable: true },
 *     { key: 'status', title: 'Status', render: (v) => <Badge>{v}</Badge> }
 *   ]}
 *   data={users}
 * />
 * ```
 */
export function DataTable<T = any>({
  className,
  columns,
  data,
  loading = false,
  emptyMessage = "No data available",
  onRowClick,
  sortable = true,
  hoverable = true,
  striped = false,
  compact = false,
  ...props
}: DataTableProps<T>) {
  const [sortKey, setSortKey] = React.useState<string | null>(null);
  const [sortDirection, setSortDirection] = React.useState<"asc" | "desc">(
    "asc",
  );

  const handleSort = (key: string) => {
    if (!sortable) return;

    if (sortKey === key) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDirection("asc");
    }
  };

  const sortedData = React.useMemo(() => {
    if (!sortKey) return data;

    return [...data].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];

      if (aVal === bVal) return 0;

      const comparison = aVal > bVal ? 1 : -1;
      return sortDirection === "asc" ? comparison : -comparison;
    });
  }, [data, sortKey, sortDirection]);

  return (
    <div
      className={cn(
        [
          "w-full overflow-auto",
          "bg-[var(--card)]",
          "border border-[var(--border)]",
          "rounded-[var(--radius-default)]",
          "shadow-[var(--shadow-sm)]",
        ].join(" "),
        className,
      )}
      {...props}
    >
      <table className="w-full border-collapse">
        <thead>
          <tr
            className={cn(
              ["border-b border-[var(--border)]", "bg-[var(--muted)]/30"].join(
                " ",
              ),
            )}
          >
            {columns.map((column) => (
              <th
                key={column.key}
                className={cn(
                  [
                    compact ? "px-3 py-2" : "px-4 py-3",
                    "text-[var(--text-sm)]",
                    "font-[var(--font-primary)]",
                    "font-semibold",
                    "text-[var(--foreground)]",
                    column.align === "center" && "text-center",
                    column.align === "right" && "text-right",
                    column.sortable !== false &&
                      sortable &&
                      "cursor-pointer select-none",
                    "transition-colors duration-[var(--transition-fast)]",
                    column.sortable !== false &&
                      sortable &&
                      "hover:bg-[var(--muted)]/50",
                  ].join(" "),
                )}
                style={{ width: column.width }}
                onClick={() =>
                  column.sortable !== false && handleSort(column.key)
                }
              >
                <div className="flex items-center gap-2">
                  <span>{column.title}</span>
                  {column.sortable !== false && sortable && (
                    <span>
                      {sortKey === column.key ? (
                        sortDirection === "asc" ? (
                          <ChevronUp
                            className="w-4 h-4"
                            style={{ color: "var(--primary)" }}
                          />
                        ) : (
                          <ChevronDown
                            className="w-4 h-4"
                            style={{ color: "var(--primary)" }}
                          />
                        )
                      ) : (
                        <ChevronsUpDown className="w-4 h-4 text-[var(--muted-foreground)]" />
                      )}
                    </span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>

        <tbody>
          {loading ? (
            <tr>
              <td colSpan={columns.length} className="p-8 text-center">
                <div className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-[var(--primary)] border-t-transparent rounded-full animate-spin" />
                  <span className="text-[var(--text-sm)] font-[var(--font-primary)] text-[var(--muted-foreground)]">
                    Loading...
                  </span>
                </div>
              </td>
            </tr>
          ) : sortedData.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="p-8 text-center">
                <p className="text-[var(--text-sm)] font-[var(--font-primary)] text-[var(--muted-foreground)]">
                  {emptyMessage}
                </p>
              </td>
            </tr>
          ) : (
            sortedData.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className={cn(
                  [
                    "border-b border-[var(--border)] last:border-0",
                    striped && rowIndex % 2 === 1 && "bg-[var(--muted)]/20",
                    hoverable && "hover:bg-[var(--muted)]/30",
                    onRowClick && "cursor-pointer",
                    "transition-colors duration-[var(--transition-fast)]",
                  ].join(" "),
                )}
                onClick={() => onRowClick?.(row, rowIndex)}
              >
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className={cn(
                      [
                        compact ? "px-3 py-2" : "px-4 py-3",
                        "text-[var(--text-sm)]",
                        "font-[var(--font-primary)]",
                        "text-[var(--foreground)]",
                        column.align === "center" && "text-center",
                        column.align === "right" && "text-right",
                      ].join(" "),
                    )}
                  >
                    {column.render
                      ? column.render(row[column.key], row, rowIndex)
                      : row[column.key]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

DataTable.displayName = "DataTable";

export type { Column };
