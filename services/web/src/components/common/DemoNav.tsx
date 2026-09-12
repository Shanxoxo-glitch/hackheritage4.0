import { useState, useRef, useEffect } from "react";
import { Link, useLocation } from "@tanstack/react-router";
import { Compass, HeartHandshake, Stethoscope, BarChart3, ChevronUp, Layers, Power, Scale, Download } from "lucide-react";
import { getCurrentUser, logoutUser, subscribeToStore, AuthUser } from "@/lib/store";

export function DemoNav() {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  const currentPath = location.pathname;
  const navRef = useRef<HTMLDivElement>(null);
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    const refresh = () => setCurrentUser(getCurrentUser());
    refresh();
    const unsub = subscribeToStore(refresh);
    return () => unsub();
  }, []);

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (navRef.current && !navRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      window.addEventListener("mousedown", handleClickOutside);
      return () => window.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isOpen]);

  return (
    <div ref={navRef} className="fixed bottom-4 right-4 z-50 flex flex-col items-end">
      {/* Smoothly animated popup menu */}
      <div
        className={`mb-3 w-72 rounded-2xl border border-foreground/15 bg-card/95 p-3.5 text-foreground shadow-[0_25px_60px_-15px_rgba(0,0,0,0.25)] backdrop-blur-md transition-all duration-300 ease-out origin-bottom-right ${
          isOpen
            ? "opacity-100 scale-100 translate-y-0 pointer-events-auto"
            : "opacity-0 scale-95 translate-y-3 pointer-events-none"
        }`}
      >
        <div className="mb-2.5 flex items-center justify-between border-b border-foreground/10 pb-2 px-1">
          <span className="text-xs font-semibold uppercase tracking-widest text-clay">
            Role Switcher
          </span>
          <span className="text-[10px] text-foreground/50 font-mono">Hackathon Navigator</span>
        </div>

        <div className="space-y-1 text-xs">
          <div className="px-1 text-[10px] font-medium text-foreground/40 uppercase tracking-wider">
            Victim Sanctuary
          </div>
          <div className="grid grid-cols-2 gap-1">
            <Link
              to="/"
              onClick={() => setIsOpen(false)}
              className={`rounded-lg px-2.5 py-1.5 transition-colors ${
                currentPath === "/" ? "bg-forest text-forest-foreground font-medium" : "hover:bg-foreground/5"
              }`}
            >
              Home
            </Link>
            <Link
              to="/checkin"
              onClick={() => setIsOpen(false)}
              className={`rounded-lg px-2.5 py-1.5 transition-colors ${
                currentPath === "/checkin" ? "bg-forest text-forest-foreground font-medium" : "hover:bg-foreground/5"
              }`}
            >
              Check-in
            </Link>
            <Link
              to="/chat"
              onClick={() => setIsOpen(false)}
              className={`rounded-lg px-2.5 py-1.5 transition-colors ${
                currentPath === "/chat" ? "bg-forest text-forest-foreground font-medium" : "hover:bg-foreground/5"
              }`}
            >
              Crisis Chat
            </Link>
            <Link
              to="/history"
              onClick={() => setIsOpen(false)}
              className={`rounded-lg px-2.5 py-1.5 transition-colors ${
                currentPath === "/history" ? "bg-forest text-forest-foreground font-medium" : "hover:bg-foreground/5"
              }`}
            >
              Garden
            </Link>
            <Link
              to="/request"
              onClick={() => setIsOpen(false)}
              className={`rounded-lg px-2.5 py-1.5 transition-colors ${
                currentPath === "/request" ? "bg-forest text-forest-foreground font-medium" : "hover:bg-foreground/5"
              }`}
            >
              Get Help
            </Link>
            <Link
              to="/status"
              onClick={() => setIsOpen(false)}
              className={`rounded-lg px-2.5 py-1.5 transition-colors ${
                currentPath === "/status" ? "bg-forest text-forest-foreground font-medium" : "hover:bg-foreground/5"
              }`}
            >
              Case Status
            </Link>
          </div>

          <div className="pt-2 px-1 text-[10px] font-medium text-foreground/40 uppercase tracking-wider">
            Counsellor Field Office
          </div>
          <div className="space-y-0.5">
            <Link
              to="/counsellor"
              onClick={() => setIsOpen(false)}
              className={`flex items-center gap-2 rounded-lg px-2.5 py-1.5 transition-colors ${
                currentPath === "/counsellor" ? "bg-forest text-forest-foreground font-medium" : "hover:bg-foreground/5"
              }`}
            >
              <Stethoscope className="h-3.5 w-3.5 text-clay" />
              <span>Assigned Cases & Field Notes</span>
            </Link>
            <Link
              to="/casewriter"
              onClick={() => setIsOpen(false)}
              className={`flex items-center gap-2 rounded-lg px-2.5 py-1.5 transition-colors ${
                currentPath === "/casewriter" ? "bg-forest text-forest-foreground font-medium" : "hover:bg-foreground/5"
              }`}
            >
              <Scale className="h-3.5 w-3.5 text-clay" />
              <span>CaseWriter Clinical Studio</span>
            </Link>
            <Link
              to="/counsellor/alerts"
              onClick={() => setIsOpen(false)}
              className={`flex items-center gap-2 rounded-lg px-2.5 py-1.5 transition-colors ${
                currentPath === "/counsellor/alerts" ? "bg-forest text-forest-foreground font-medium" : "hover:bg-foreground/5"
              }`}
            >
              <HeartHandshake className="h-3.5 w-3.5 text-clay" />
              <span>Alert Queue & Escalations</span>
            </Link>
            <Link
              to="/counsellor/trace/$threadId"
              params={{ threadId: "thread-8492" }}
              onClick={() => setIsOpen(false)}
              className={`flex items-center gap-2 rounded-lg px-2.5 py-1.5 transition-colors ${
                currentPath.includes("/trace") ? "bg-forest text-forest-foreground font-medium" : "hover:bg-foreground/5"
              }`}
            >
              <Layers className="h-3.5 w-3.5 text-clay" />
              <span>AI Decision Trace Audit</span>
            </Link>
          </div>

          <div className="pt-2 px-1 text-[10px] font-medium text-foreground/40 uppercase tracking-wider">
            Admin & Triage
          </div>
          <Link
            to="/admin"
            onClick={() => setIsOpen(false)}
            className={`flex items-center gap-2 rounded-lg px-2.5 py-1.5 transition-colors ${
              currentPath === "/admin" ? "bg-forest text-forest-foreground font-medium" : "hover:bg-foreground/5"
            }`}
          >
            <BarChart3 className="h-3.5 w-3.5 text-sage-deep" />
            <span>Observatory Dashboard</span>
          </Link>

          <div className="pt-2 border-t border-foreground/10 px-1">
            <button
              onClick={() => {
                sessionStorage.removeItem("sahayak_pwa_dismissed");
                const promptEvent = (window as unknown as { __deferredPwaPrompt?: { prompt: () => Promise<void> } }).__deferredPwaPrompt;
                if (promptEvent) {
                  promptEvent.prompt();
                } else {
                  alert("To install Sahayak:\\n\\n• Desktop Chrome/Edge: Click the Install icon in the address bar (next to the star icon) or ⋮ menu -> 'Install Sahayak'.\\n• iOS Safari: Tap Share (📤) -> 'Add to Home Screen'.");
                }
                setIsOpen(false);
              }}
              className="w-full flex items-center justify-between gap-2 rounded-lg px-2.5 py-1.5 bg-forest/10 hover:bg-forest/20 text-forest text-xs font-medium transition-colors"
            >
              <div className="flex items-center gap-2">
                <Download className="h-3.5 w-3.5" />
                <span>Install Sahayak App</span>
              </div>
              <span className="text-[10px] bg-forest text-white px-1.5 py-0.2 rounded-full font-sans">PWA</span>
            </button>
          </div>

          {currentUser && (
            <div className="border-t border-foreground/10 pt-2 flex items-center justify-between px-1 text-[11px]">
              <div className="flex flex-col min-w-0 pr-2">
                <span className="text-[9px] uppercase tracking-wider text-foreground/45">Active Session</span>
                <span className="font-mono truncate font-medium text-foreground text-[10px]">
                  {currentUser.name} ({currentUser.role})
                </span>
              </div>
              <button
                type="button"
                onClick={() => {
                  logoutUser();
                  setIsOpen(false);
                }}
                className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-forest text-white shadow-sm hover:bg-clay transition-all cursor-pointer"
                title="Log out from current session"
                aria-label="Log out"
              >
                <Power className="h-3 w-3 text-white" />
              </button>
            </div>
          )}

          <div className="border-t border-foreground/10 pt-2">
            <Link
              to="/portal"
              onClick={() => setIsOpen(false)}
              className="block text-center rounded-lg bg-foreground/5 py-1.5 text-[11px] font-medium hover:bg-clay hover:text-white transition-colors"
            >
              View Full Multi-Role Portal
            </Link>
          </div>
        </div>
      </div>

      {/* Trigger Button - Anchor position remains completely static */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        type="button"
        className="flex items-center gap-2 rounded-full border border-forest/20 bg-forest px-4 py-2 text-xs font-medium text-forest-foreground shadow-[0_10px_25px_-5px_rgba(0,0,0,0.25)] transition-all duration-200 hover:scale-105 active:scale-95 cursor-pointer"
        aria-expanded={isOpen}
      >
        <Compass className="h-3.5 w-3.5 text-clay" />
        <span>Explore Roles</span>
        <ChevronUp className={`h-3.5 w-3.5 transition-transform duration-300 ease-out ${isOpen ? "rotate-180" : ""}`} />
      </button>
    </div>
  );
}
