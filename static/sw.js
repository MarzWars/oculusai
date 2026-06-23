const CACHE_NAME = 'oculus-v1';
const ASSETS = [
  '/',
  '/static/style.css',
  '/static/oculus.js',
  '/static/oculus_avatar.svg',
  '/static/oculus_logo.svg',
  '/static/favicon.ico'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET' || !e.request.url.startsWith(self.location.origin)) {
    return;
  }
  
  e.respondWith(
    caches.match(e.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(e.request).then((response) => {
        // Do not cache active APIs, templates, asks, logins, or sessions
        const url = e.request.url;
        if (
          url.includes('/api/') || 
          url.includes('/ask') || 
          url.includes('/login') || 
          url.includes('/register') || 
          url.includes('/logout') || 
          url.includes('/clear')
        ) {
          return response;
        }
        return caches.open(CACHE_NAME).then((cache) => {
          cache.put(e.request, response.clone());
          return response;
        });
      });
    })
  );
});
