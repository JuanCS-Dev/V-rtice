import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Shield,
  ShieldAlert,
  Search,
  Brain,
  HeartPulse,
  Network,
  Database,
  Settings,
  Lock,
} from "lucide-react";
import { useUIStore } from "@/stores/uiStore";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Offensive", href: "/offensive", icon: ShieldAlert },
  { name: "Defensive", href: "/defensive", icon: Shield },
  { name: "OSINT", href: "/osint", icon: Search },
  { name: "MAXIMUS", href: "/maximus", icon: Brain },
  { name: "Immunis", href: "/immunis", icon: HeartPulse },
  { name: "Reactive Fabric", href: "/reactive-fabric", icon: Network },
  { name: "SINESP", href: "/sinesp", icon: Database },
  { name: "Admin", href: "/admin", icon: Lock },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const { sidebarOpen } = useUIStore();

  if (!sidebarOpen) return null;

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-[rgb(var(--border))] bg-[rgb(var(--card))]/95 backdrop-blur-xl transition-all duration-300">
      {/* Logo/Brand */}
      <div className="flex h-14 items-center gap-2.5 border-b border-[rgb(var(--border))] px-4">
        <div className="relative">
          <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-primary-500 to-primary-600 shadow-md shadow-primary-500/25 ring-1 ring-primary-500/20" />
          <div className="absolute inset-0 h-7 w-7 rounded-lg bg-gradient-to-br from-primary-400/30 to-transparent" />
        </div>
        <div className="flex flex-col leading-none">
          <span className="text-sm font-bold tracking-tight text-[rgb(var(--text-primary))]">
            Vértice
          </span>
          <span className="text-[9px] font-semibold text-[rgb(var(--text-tertiary))] mt-0.5 tracking-wider">
            v3.3.1
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="space-y-0.5 p-2.5">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              cn(
                "group relative flex items-center gap-2.5 rounded-lg px-3 py-2 text-xs font-semibold transition-all duration-200 ease-out",
                isActive
                  ? "bg-primary-500/10 text-primary-600 dark:bg-primary-500/20 dark:text-primary-400 shadow-sm"
                  : "text-[rgb(var(--text-secondary))] hover:bg-gray-100/80 hover:text-[rgb(var(--text-primary))] dark:hover:bg-gray-800/50 hover:translate-x-0.5 active:scale-[0.98]",
              )
            }
          >
            {({ isActive }) => (
              <>
                {/* Active indicator */}
                {isActive && (
                  <div className="absolute left-0 top-1/2 h-4 w-1 -translate-y-1/2 rounded-r-full bg-primary-500 shadow-sm" />
                )}

                {/* Icon with subtle animation */}
                <item.icon
                  className={cn(
                    "h-4 w-4 transition-all duration-200 group-hover:scale-110",
                    isActive && "text-primary-600 dark:text-primary-400",
                  )}
                  strokeWidth={2.5}
                />

                {/* Label */}
                <span className="flex-1 leading-none">{item.name}</span>

                {/* Subtle hover glow */}
                {isActive && (
                  <div className="absolute inset-0 -z-10 rounded-lg bg-primary-500/5 blur-sm" />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
