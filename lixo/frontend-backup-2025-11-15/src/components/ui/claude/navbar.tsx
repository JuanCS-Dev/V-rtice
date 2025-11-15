/**
 * ═══════════════════════════════════════════════════════════════════════════
 * NAVBAR COMPONENT - CLAUDE.AI GREEN STYLE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * REESCRITO DO ZERO - NÃO é adaptação
 * Baseado em: Claude.ai top navigation
 * Estilo: Clean, minimal, sticky, backdrop blur
 */

import * as React from "react"
import { Menu, X, ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "./button"
import { Badge } from "./badge"
import "../../../styles/claude-design-green.css"

export interface NavbarProps extends React.HTMLAttributes<HTMLElement> {
  /**
   * Logo or brand component
   */
  logo?: React.ReactNode
  /**
   * Navigation items
   */
  navItems?: NavItem[]
  /**
   * Right side actions
   */
  actions?: React.ReactNode
  /**
   * Mobile menu open state
   */
  mobileMenuOpen?: boolean
  /**
   * Toggle mobile menu
   */
  onMobileMenuToggle?: () => void
  /**
   * Sticky positioning
   */
  sticky?: boolean
  /**
   * Show border bottom
   */
  bordered?: boolean
}

export interface NavItem {
  label: string
  href?: string
  onClick?: () => void
  badge?: string
  active?: boolean
  disabled?: boolean
  children?: NavItem[]
}

/**
 * Navbar Component - Claude.ai Green Style
 *
 * Clean top navigation with backdrop blur
 *
 * Usage:
 * ```tsx
 * <Navbar
 *   logo={<Logo />}
 *   navItems={[
 *     { label: 'Home', href: '/', active: true },
 *     { label: 'About', href: '/about' },
 *   ]}
 *   actions={<Button size="sm">Sign In</Button>}
 * />
 * ```
 */
export const Navbar = React.forwardRef<HTMLElement, NavbarProps>(
  (
    {
      className,
      logo,
      navItems = [],
      actions,
      mobileMenuOpen = false,
      onMobileMenuToggle,
      sticky = true,
      bordered = true,
      children,
      ...props
    },
    ref
  ) => {
    const [openDropdown, setOpenDropdown] = React.useState<string | null>(null)

    return (
      <>
        {/* Main Navbar */}
        <nav
          ref={ref}
          className={cn(
            [
              // Layout
              "w-full",
              "z-[var(--z-sticky)]",
              // Background - Claude.ai style
              "bg-[var(--sidebar-background)]",
              "backdrop-blur-[var(--blur-md)]",
              // Border
              bordered && "border-b border-[var(--sidebar-border)]",
              // Shadow
              "shadow-[var(--shadow-sm)]",
              // Sticky
              sticky && "sticky top-0",
              // Transition
              "transition-all duration-[var(--transition-normal)]",
            ].join(" "),
            className
          )}
          {...props}
        >
          <div className="max-w-[1400px] mx-auto px-[var(--space-4)]">
            <div className="flex items-center justify-between h-16">
              {/* Logo */}
              <div className="flex-shrink-0">
                {logo || (
                  <div
                    className="text-[var(--text-xl)] font-[var(--font-display)] font-bold"
                    style={{ color: "var(--primary)" }}
                  >
                    VÉRTICE 💚
                  </div>
                )}
              </div>

              {/* Desktop Navigation */}
              <div className="hidden md:flex items-center gap-[var(--space-1)]">
                {navItems.map((item, index) => (
                  <NavItemComponent
                    key={index}
                    item={item}
                    isOpen={openDropdown === item.label}
                    onToggle={() =>
                      setOpenDropdown(
                        openDropdown === item.label ? null : item.label
                      )
                    }
                  />
                ))}
              </div>

              {/* Actions */}
              <div className="hidden md:flex items-center gap-[var(--space-2)]">
                {actions}
              </div>

              {/* Mobile Menu Button */}
              <div className="md:hidden">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onMobileMenuToggle}
                  aria-label="Toggle menu"
                >
                  {mobileMenuOpen ? (
                    <X className="h-5 w-5" />
                  ) : (
                    <Menu className="h-5 w-5" />
                  )}
                </Button>
              </div>
            </div>

            {/* Custom children */}
            {children}
          </div>
        </nav>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div
            className={cn([
              "md:hidden",
              "fixed inset-x-0 top-16",
              "z-[var(--z-sticky)]",
              "bg-[var(--sidebar-background)]",
              "border-b border-[var(--sidebar-border)]",
              "shadow-[var(--shadow-lg)]",
              "backdrop-blur-[var(--blur-md)]",
              "max-h-[calc(100vh-4rem)]",
              "overflow-y-auto",
            ].join(" "))}
          >
            <div className="px-[var(--space-4)] py-[var(--space-4)] space-y-[var(--space-2)]">
              {navItems.map((item, index) => (
                <MobileNavItem key={index} item={item} />
              ))}

              {actions && (
                <div className="pt-[var(--space-4)] border-t border-[var(--sidebar-border)]">
                  {actions}
                </div>
              )}
            </div>
          </div>
        )}
      </>
    )
  }
)

Navbar.displayName = "Navbar"

/**
 * Desktop Nav Item
 */
function NavItemComponent({
  item,
  isOpen,
  onToggle,
}: {
  item: NavItem
  isOpen: boolean
  onToggle: () => void
}) {
  const hasChildren = item.children && item.children.length > 0

  if (hasChildren) {
    return (
      <div className="relative">
        <button
          onClick={onToggle}
          disabled={item.disabled}
          className={cn([
            "flex items-center gap-[var(--space-1)]",
            "px-[var(--space-3)] py-[var(--space-2)]",
            "text-[var(--text-sm)]",
            "font-[var(--font-primary)]",
            "font-medium",
            "rounded-[var(--radius-md)]",
            "transition-all duration-[var(--transition-fast)]",
            // States
            item.active
              ? "bg-[var(--sidebar-accent)] text-[var(--sidebar-primary)]"
              : "text-[var(--sidebar-foreground)] hover:bg-[var(--sidebar-accent)]",
            item.disabled && "opacity-50 cursor-not-allowed",
          ].join(" "))}
        >
          {item.label}
          {item.badge && (
            <Badge variant="success" className="ml-2">
              {item.badge}
            </Badge>
          )}
          <ChevronDown
            className={cn(
              "h-4 w-4 transition-transform",
              isOpen && "rotate-180"
            )}
          />
        </button>

        {/* Dropdown */}
        {isOpen && (
          <div
            className={cn([
              "absolute top-full left-0 mt-1",
              "min-w-[200px]",
              "bg-[var(--popover)]",
              "border border-[var(--border)]",
              "rounded-[var(--radius-default)]",
              "shadow-[var(--shadow-lg)]",
              "py-[var(--space-2)]",
              "z-[var(--z-dropdown)]",
            ].join(" "))}
          >
            {item.children?.map((child, index) => (
              <a
                key={index}
                href={child.href}
                onClick={child.onClick}
                className={cn([
                  "block px-[var(--space-4)] py-[var(--space-2)]",
                  "text-[var(--text-sm)]",
                  "font-[var(--font-primary)]",
                  "text-[var(--foreground)]",
                  "hover:bg-[var(--accent)]",
                  "transition-colors duration-[var(--transition-fast)]",
                  child.active && "bg-[var(--accent)] text-[var(--primary)]",
                ].join(" "))}
              >
                {child.label}
              </a>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <a
      href={item.href}
      onClick={item.onClick}
      className={cn([
        "flex items-center gap-[var(--space-2)]",
        "px-[var(--space-3)] py-[var(--space-2)]",
        "text-[var(--text-sm)]",
        "font-[var(--font-primary)]",
        "font-medium",
        "rounded-[var(--radius-md)]",
        "transition-all duration-[var(--transition-fast)]",
        // States
        item.active
          ? "bg-[var(--sidebar-accent)] text-[var(--sidebar-primary)]"
          : "text-[var(--sidebar-foreground)] hover:bg-[var(--sidebar-accent)]",
        item.disabled && "opacity-50 cursor-not-allowed pointer-events-none",
      ].join(" "))}
    >
      {item.label}
      {item.badge && (
        <Badge variant="success" className="ml-2">
          {item.badge}
        </Badge>
      )}
    </a>
  )
}

/**
 * Mobile Nav Item
 */
function MobileNavItem({ item }: { item: NavItem }) {
  const [expanded, setExpanded] = React.useState(false)
  const hasChildren = item.children && item.children.length > 0

  return (
    <div>
      <button
        onClick={() => {
          if (hasChildren) {
            setExpanded(!expanded)
          } else {
            item.onClick?.()
          }
        }}
        disabled={item.disabled}
        className={cn([
          "w-full flex items-center justify-between",
          "px-[var(--space-4)] py-[var(--space-3)]",
          "text-[var(--text-base)]",
          "font-[var(--font-primary)]",
          "font-medium",
          "rounded-[var(--radius-md)]",
          "transition-all duration-[var(--transition-fast)]",
          // States
          item.active
            ? "bg-[var(--sidebar-accent)] text-[var(--sidebar-primary)]"
            : "text-[var(--sidebar-foreground)] hover:bg-[var(--sidebar-accent)]",
          item.disabled && "opacity-50 cursor-not-allowed",
        ].join(" "))}
      >
        <span className="flex items-center gap-2">
          {item.label}
          {item.badge && <Badge variant="success">{item.badge}</Badge>}
        </span>
        {hasChildren && (
          <ChevronDown
            className={cn(
              "h-4 w-4 transition-transform",
              expanded && "rotate-180"
            )}
          />
        )}
      </button>

      {hasChildren && expanded && (
        <div className="pl-[var(--space-4)] mt-[var(--space-1)] space-y-[var(--space-1)]">
          {item.children?.map((child, index) => (
            <a
              key={index}
              href={child.href}
              onClick={child.onClick}
              className={cn([
                "block px-[var(--space-4)] py-[var(--space-2)]",
                "text-[var(--text-sm)]",
                "font-[var(--font-primary)]",
                "text-[var(--sidebar-foreground)]",
                "rounded-[var(--radius-md)]",
                "hover:bg-[var(--sidebar-accent)]",
                "transition-colors duration-[var(--transition-fast)]",
                child.active && "bg-[var(--sidebar-accent)] text-[var(--sidebar-primary)]",
              ].join(" "))}
            >
              {child.label}
            </a>
          ))}
        </div>
      )}
    </div>
  )
}

export { NavItemComponent, MobileNavItem }
export type { NavItem }
