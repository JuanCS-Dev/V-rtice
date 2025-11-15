import { Menu, Moon, Sun, Bell } from "lucide-react";
import { Button } from "@/components/ui";
import { useUIStore } from "@/stores/uiStore";
import { useAuth } from "@/lib/auth/AuthContext";

export function Header() {
  const { toggleSidebar, theme, toggleTheme } = useUIStore();
  const { user } = useAuth();

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-[rgb(var(--border))] bg-[rgb(var(--card))]/95 px-4 backdrop-blur-xl transition-all duration-200">
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className="h-8 w-8 transition-all duration-200 hover:bg-gray-100/80 dark:hover:bg-gray-800/50 hover:scale-105 active:scale-95"
        >
          <Menu className="h-[17px] w-[17px]" strokeWidth={2} />
        </Button>
      </div>

      <div className="flex items-center gap-1">
        {/* Theme Toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          className="h-8 w-8 transition-all duration-200 hover:bg-gray-100/80 dark:hover:bg-gray-800/50 hover:scale-105 active:scale-95"
        >
          {theme === "light" ? (
            <Moon className="h-[17px] w-[17px]" strokeWidth={2} />
          ) : (
            <Sun className="h-[17px] w-[17px]" strokeWidth={2} />
          )}
        </Button>

        {/* Notifications */}
        <Button
          variant="ghost"
          size="icon"
          className="relative h-8 w-8 transition-all duration-200 hover:bg-gray-100/80 dark:hover:bg-gray-800/50 hover:scale-105 active:scale-95"
        >
          <Bell className="h-[17px] w-[17px]" strokeWidth={2} />
          {/* Notification badge */}
          <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-primary-500 ring-2 ring-[rgb(var(--card))] shadow-sm animate-pulse" />
        </Button>

        {/* Divider */}
        <div className="mx-1.5 h-5 w-px bg-[rgb(var(--border))]/50" />

        {/* User Menu */}
        <Button
          variant="ghost"
          size="sm"
          className="h-8 gap-2 px-2.5 transition-all duration-200 hover:bg-gray-100/80 dark:hover:bg-gray-800/50 hover:scale-105 active:scale-95"
        >
          <div className="flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-br from-primary-500 to-primary-600 text-[10px] font-bold text-white shadow-sm ring-1 ring-primary-500/20">
            {user?.username?.[0]?.toUpperCase() || "U"}
          </div>
          <span className="text-xs font-semibold text-[rgb(var(--text-primary))] leading-none">
            {user?.username || "User"}
          </span>
        </Button>
      </div>
    </header>
  );
}
