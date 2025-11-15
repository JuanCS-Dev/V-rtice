import { Heart } from "lucide-react";

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-[rgb(var(--border))] bg-[rgb(var(--card))]/80 backdrop-blur-xl">
      <div className="mx-auto max-w-7xl px-6 py-3">
        <div className="flex items-center justify-center gap-3 text-sm text-[rgb(var(--text-secondary))]">
          {/* Year - sempre visível */}
          <span className="text-xs">© {currentYear}</span>

          <span className="text-[rgb(var(--border))]">•</span>

          {/* Soli Deo Gloria - sempre visível */}
          <div className="flex items-center gap-1.5">
            <span className="font-medium text-[rgb(var(--text-primary))]">
              Soli Deo Gloria
            </span>
            <Heart className="h-3 w-3 text-primary-500 fill-primary-500" />
          </div>

          <span className="hidden sm:inline text-[rgb(var(--border))]">•</span>

          {/* Version - visível em telas maiores */}
          <span className="hidden sm:inline text-xs">v3.3.1</span>
        </div>
      </div>
    </footer>
  );
}
