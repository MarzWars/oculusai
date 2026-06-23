const CACHE_NAME = 'oculus-v2';
// Only cache truly static assets — never the root HTML (it's server-rendered & dynamic)
const ASSETS = [
  '/static/style.css',
  '/static/oculus.js',
  '/static/oculus_avatar.svg',
  '/static/oculus_logo.svg',
  '/static/favicon.ico'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.map((key) => key !== CACHE_NAME && caches.delete(key)))
    ).then(() => self.clients.claim())
  );
});

// Dynamic / authenticated routes — always go to network
const BYPASS = ['/', '/ask', '/clear', '/set_model', '/login', '/register', '/logout', '/brain', '/api/'];

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET' || !e.request.url.startsWith(self.location.origin)) return;

  const path = new URL(e.request.url).pathname;
  if (BYPASS.some(b => path === b || path.startsWith(b))) {
    // Always network-first for dynamic routes
    e.respondWith(fetch(e.request));
    return;
  }

  e.respondWith(
    caches.match(e.request).then((cached) => {
      if (cached) return cached;
      return fetch(e.request).then((response) => {
        caches.open(CACHE_NAME).then((cache) => cache.put(e.request, response.clone()));
        return response;
      });
    })
  );
});