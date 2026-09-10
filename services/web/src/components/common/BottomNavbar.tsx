import { Link, useLocation } from "@tanstack/react-router";
import {
  MessageCircle,
  User,
} from "lucide-react";

interface BottomNavbarProps {
  onOpenAuth: () => void;
}

export function BottomNavbar({ onOpenAuth }: BottomNavbarProps) {
  const location = useLocation();
  const currentPath = location.pathname;

  return (
      <nav
        className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 w-auto max-w-[94vw] rounded-full border border-foreground/15 bg-card/90 px-3 py-2 shadow-[0_20px_50px_-10px_rgba(0,0,0,0.25)] backdrop-blur-md flex items-center gap-1.5 sm:gap-2.5 transition-all"
        aria-label="Bottom primary navigation"
      >
        {/* Brand / Home Link */}
        <Link
          to="/"
          className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
            currentPath === "/"
              ? "bg-foreground/10 text-foreground font-semibold"
              : "text-foreground/70 hover:text-foreground hover:bg-foreground/5"
          }`}
          title="Sanctuary Home"
        >
          <span className="font-display text-sm tracking-tight">Sahayak</span>
        </Link>

        {/* Check-in Quick Link */}
        <Link
          to="/checkin"
          className={`hidden sm:inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
            currentPath === "/checkin"
              ? "bg-foreground/10 text-foreground font-semibold"
              : "text-foreground/70 hover:text-foreground hover:bg-foreground/5"
          }`}
        >
          <span>Check-in</span>
        </Link>

        {/* Garden Quick Link */}
        <Link
          to="/history"
          className={`hidden md:inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
            currentPath === "/history"
              ? "bg-foreground/10 text-foreground font-semibold"
              : "text-foreground/70 hover:text-foreground hover:bg-foreground/5"
          }`}
        >
          <span>Garden</span>
        </Link>

        {/* REQ: Enter chat in white texts inside a green rounded button */}
        <Link
          to="/chat"
          className="inline-flex items-center gap-1.5 rounded-full bg-forest hover:bg-forest-deep text-white font-medium px-4 sm:px-5 py-2 text-xs sm:text-sm shadow-[var(--shadow-lift)] transition-all hover:scale-105 active:scale-95 whitespace-nowrap"
        >
          <MessageCircle className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-white" />
          <span className="text-white font-medium tracking-wide">Enter Chat</span>
        </Link>

        {/* Sign in / Login modal button */}
        <button
          type="button"
          onClick={onOpenAuth}
          className="flex items-center gap-1 rounded-full p-2 text-foreground/70 hover:text-clay hover:bg-foreground/5 transition-colors"
          title="Sign in or register role"
          aria-label="Account login and registration"
        >
          <User className="h-4 w-4" />
        </button>
      </nav>
  );
}
