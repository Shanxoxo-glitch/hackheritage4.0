const CACHE_NAME = "sahayak-pwa-v2";

const STATIC_PRECACHE = [
  "/",
  "/checkin",
  "/history",
  "/chat",
  "/casewriter",
  "/request",
  "/status",
  "/help",
  "/counsellor",
  "/counsellor/alerts",
  "/portal",
  "/manifest.json",
  "/favicon.ico",
  "/icon-192.png",
  "/icon-512.png",
  "/apple-touch-icon.png",
  "/icon.svg"
];

// Install: precache static routes and assets
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_PRECACHE).catch((err) => {
        console.warn("[SW] Precache partial error (non-fatal):", err);
      });
    })
  );
  self.skipWaiting();
});

// Activate: purge old cache versions
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      )
    )
  );
  self.clients.claim();
});

// Fetch: network-first for navigation, stale-while-revalidate for assets, skip live APIs
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // 1. Never cache non-GET requests or backend streaming APIs
  if (request.method !== "GET" || url.pathname.includes("/v1/") || url.pathname.includes("/api/")) {
    return;
  }

  // 2. Navigation requests: Network first with offline fallback to cached page or home
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return response;
        })
        .catch(async () => {
          const cached = await caches.match(request);
          if (cached) return cached;
          const home = await caches.match("/");
          if (home) return home;
          return new Response(
            "<!DOCTYPE html><html><body style='font-family:sans-serif;text-align:center;padding:50px;background:#f1ece4;'><h2>Offline — Sahayak Sanctuary</h2><p>Your local sanctuary is loaded from offline cache. Please reconnect when possible.</p><a href='/' style='color:#2d4a3e;font-weight:bold;'>Return to Sanctuary</a></body></html>",
            { headers: { "Content-Type": "text/html" } }
          );
        })
    );
    return;
  }

  // 3. Static assets (JS, CSS, fonts, images): Cache first with network revalidation
  if (
    url.pathname.startsWith("/assets/") ||
    url.pathname.endsWith(".css") ||
    url.pathname.endsWith(".js") ||
    url.pathname.endsWith(".png") ||
    url.pathname.endsWith(".webp") ||
    url.pathname.endsWith(".avif") ||
    url.pathname.endsWith(".ico") ||
    url.pathname.endsWith(".svg") ||
    url.hostname.includes("fonts.gstatic.com") ||
    url.hostname.includes("fonts.googleapis.com")
  ) {
    event.respondWith(
      caches.match(request).then((cached) => {
        const fetchPromise = fetch(request)
          .then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200) {
              const clone = networkResponse.clone();
              caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
            }
            return networkResponse;
          })
          .catch(() => cached);

        return cached || fetchPromise;
      })
    );
    return;
  }

  // Default: Network with cache fallback
  event.respondWith(
    fetch(request).catch(() => caches.match(request))
  );
});

// Allow clients to trigger skipWaiting manually
self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});