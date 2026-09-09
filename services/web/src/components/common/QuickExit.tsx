import { useEffect, useCallback } from "react";
import { useLocation } from "@tanstack/react-router";
import { executeQuickExit } from "@/lib/store";
import { ShieldAlert } from "lucide-react";

export function QuickExit() {
  const location = useLocation();
  const path = location.pathname;

  // Quick exit is strictly for victim views only — never on counsellor, admin, or portal screens
  const isVictimScreen =
    !path.startsWith("/counsellor") &&
    !path.startsWith("/admin") &&
    !path.startsWith("/portal");

  const exit = useCallback(() => {
    executeQuickExit();
  }, []);

  useEffect(() => {
    if (!isVictimScreen) return;

    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        exit();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [exit, isVictimScreen]);

  if (!isVictimScreen) {
    return null;
  }

  return (
    <button
      onClick={exit}
      type="button"
      title="Quick Exit (Esc) — Immediately clears browsing history and switches page"
      className="fixed top-4 right-4 z-50 flex items-center gap-2 rounded-full border border-clay/30 bg-card/90 px-3 py-1.5 text-xs font-medium text-foreground/80 shadow-[var(--shadow-lift)] backdrop-blur-md transition-all hover:bg-clay hover:text-white group"
      aria-label="Quick exit to safe page"
    >
      <ShieldAlert className="h-3.5 w-3.5 text-clay transition-colors group-hover:text-white" />
      <span>Quick Exit</span>
      <kbd className="hidden sm:inline-block rounded bg-foreground/10 px-1.5 py-0.5 text-[10px] font-mono text-foreground/70 group-hover:bg-white/20 group-hover:text-white">
        Esc
      </kbd>
    </button>
  );
}
