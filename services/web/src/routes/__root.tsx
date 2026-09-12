import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";
import { type ReactNode, useEffect } from "react";

import appCss from "../styles.css?url";
import { reportLovableError } from "../lib/lovable-error-reporting";
import { QuickExit } from "../components/common/QuickExit";
import { DemoNav } from "../components/common/DemoNav";
import { SplineLoadingScreen } from "../components/common/SplineLoadingScreen";
import { PwaInstallPrompt } from "../components/common/PwaInstallPrompt";

function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-7xl font-bold text-foreground font-display">404</h1>
        <h2 className="mt-4 text-xl font-semibold text-foreground">A quiet detour</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          This path doesn't lead anywhere right now. Let's head back together.
        </p>
        <div className="mt-6">
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-full bg-forest px-6 py-2.5 text-sm font-medium text-forest-foreground transition-colors hover:bg-clay"
          >
            Return to Sanctuary
          </Link>
        </div>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  console.error(error);
  const router = useRouter();
  useEffect(() => {
    reportLovableError(error, { boundary: "tanstack_root_error_component" });
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-xl font-semibold tracking-tight text-foreground font-display">
          Taking a quiet pause
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Something stumbled while rendering this view. You can try refreshing or return home.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="inline-flex items-center justify-center rounded-full bg-forest px-5 py-2 text-sm font-medium text-forest-foreground transition-colors hover:bg-clay"
          >
            Try again
          </button>
          <a
            href="/"
            className="inline-flex items-center justify-center rounded-full border border-foreground/20 bg-background px-5 py-2 text-sm font-medium text-foreground transition-colors hover:bg-card"
          >
            Return Home
          </a>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1, maximum-scale=1" },
      { name: "theme-color", content: "#f1ece4" },
      { title: "Sahayak — Anonymous support for heavy moments" },
      {
        name: "description",
        content:
          "Sahayak is a private, anonymous sanctuary to steady yourself, unburden, and connect with support when you're ready.",
      },
      { property: "og:title", content: "Sahayak — Anonymous support for heavy moments" },
      {
        property: "og:description",
        content:
          "A quiet, anonymous sanctuary for the moments that feel too heavy to carry alone.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "application-name", content: "Sahayak" },
      { name: "apple-mobile-web-app-capable", content: "yes" },
      { name: "apple-mobile-web-app-status-bar-style", content: "default" },
      { name: "apple-mobile-web-app-title", content: "Sahayak" },
      { name: "mobile-web-app-capable", content: "yes" },
      { name: "msapplication-TileColor", content: "#f1ece4" },
      { name: "msapplication-TileImage", content: "/icon-192.png" },
      { name: "msapplication-tap-highlight", content: "no" },
    ],
    links: [
      {
        rel: "stylesheet",
        href: appCss,
      },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Work+Sans:wght@300;400;500;600&display=swap",
      },
      { rel: "manifest", href: "/manifest.json" },
      { rel: "icon", href: "/favicon.ico", type: "image/x-icon" },
      { rel: "icon", href: "/icon-192.png", type: "image/png", sizes: "192x192" },
      { rel: "icon", href: "/icon.svg", type: "image/svg+xml" },
      { rel: "apple-touch-icon", href: "/apple-touch-icon.png", sizes: "180x180" },
    ],
  }),

  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();

  useEffect(() => {
    if (typeof window !== "undefined" && "serviceWorker" in navigator) {
      window.addEventListener("load", () => {
        navigator.serviceWorker
          .register("/sw.js")
          .then((registration) => {
            console.log("[Sahayak PWA] Service worker registered successfully. Scope:", registration.scope);
          })
          .catch((error) => {
            console.warn("[Sahayak PWA] Service worker registration failed:", error);
          });
      });
    }
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <SplineLoadingScreen />
      <QuickExit />
      <PwaInstallPrompt />
      <Outlet />
      <DemoNav />
    </QueryClientProvider>
  );
}
