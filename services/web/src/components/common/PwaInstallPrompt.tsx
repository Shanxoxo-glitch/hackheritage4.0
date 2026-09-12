import { useEffect, useState } from "react";
import { Download, WifiOff, X, CheckCircle2 } from "lucide-react";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

export function PwaInstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isStandalone, setIsStandalone] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);
  const [isOffline, setIsOffline] = useState(false);
  const [justInstalled, setJustInstalled] = useState(false);

  useEffect(() => {
    // 1. Check standalone mode
    const checkStandalone = () => {
      const isWindowStandalone = window.matchMedia("(display-mode: standalone)").matches;
      const isIosStandalone = (navigator as unknown as { standalone?: boolean }).standalone === true;
      setIsStandalone(Boolean(isWindowStandalone || isIosStandalone));
    };
    checkStandalone();

    // 2. Check dismiss state in session
    if (sessionStorage.getItem("sahayak_pwa_dismissed") === "true") {
      setIsDismissed(true);
    }

    // 3. Listen for PWA install prompt
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
    };

    const handleAppInstalled = () => {
      setDeferredPrompt(null);
      setJustInstalled(true);
      setTimeout(() => setJustInstalled(false), 4000);
    };

    // 4. Listen for network status
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    if (typeof navigator !== "undefined") {
      setIsOffline(!navigator.onLine);
    }

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    window.addEventListener("appinstalled", handleAppInstalled);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
      window.removeEventListener("appinstalled", handleAppInstalled);
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  const handleInstallClick = async () => {
    if (!deferredPrompt) return;
    await deferredPrompt.prompt();
    const choice = await deferredPrompt.userChoice;
    if (choice.outcome === "accepted") {
      setDeferredPrompt(null);
    }
  };

  const handleDismiss = () => {
    setIsDismissed(true);
    sessionStorage.setItem("sahayak_pwa_dismissed", "true");
  };

  // Render Offline Sanctuary notice if offline
  if (isOffline) {
    return (
      <div className="fixed top-3 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 px-4 py-2 rounded-full bg-forest text-forest-foreground text-xs font-medium shadow-lg border border-white/10 animate-fade-in">
        <WifiOff className="w-3.5 h-3.5 text-clay" />
        <span>Offline Sanctuary Active — cached records & grounding tools ready</span>
      </div>
    );
  }

  // Render Installed toast if just completed
  if (justInstalled) {
    return (
      <div className="fixed bottom-20 sm:bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 px-4 py-2.5 rounded-full bg-forest text-white text-xs font-medium shadow-xl border border-white/20 animate-fade-in">
        <CheckCircle2 className="w-4 h-4 text-emerald-300" />
        <span>Sahayak installed to your device home screen</span>
      </div>
    );
  }

  // Do not show install prompt if dismissed, standalone, or not installable
  if (isStandalone || isDismissed || !deferredPrompt) {
    return null;
  }

  return (
    <aside aria-label="Install Sahayak Sanctuary App" className="fixed bottom-20 sm:bottom-6 right-4 sm:right-6 z-40 max-w-sm rounded-2xl bg-card/95 backdrop-blur-md p-3.5 shadow-xl border border-border text-foreground transition-all duration-300 animate-slide-up">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <img
            src="/icon-192.png"
            alt="Sahayak Icon"
            className="w-9 h-9 rounded-xl object-cover shadow-xs border border-border/50"
          />
          <div>
            <h4 className="text-xs font-semibold font-display tracking-tight text-foreground">
              Install Sahayak App
            </h4>
            <p className="text-[11px] text-muted-foreground leading-tight mt-0.5">
              Instant offline access & private home-screen sanctuary.
            </p>
          </div>
        </div>
        <button
          onClick={handleDismiss}
          className="p-1 rounded-full text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
          title="Dismiss"
          aria-label="Dismiss installation prompt"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="mt-3 flex items-center gap-2">
        <button
          onClick={handleInstallClick}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-full bg-forest text-forest-foreground text-xs font-medium hover:bg-clay transition-colors shadow-xs"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Install Sanctuary</span>
        </button>
        <button
          onClick={handleDismiss}
          className="px-3 py-1.5 rounded-full border border-border text-xs text-muted-foreground hover:text-foreground hover:bg-muted/30 transition-colors"
        >
          Later
        </button>
      </div>
    </aside>
  );
}
