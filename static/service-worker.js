const CACHE_VERSION = 'v2.7.0'; // Increment this when you update CSS/JS - UPDATED for scroll-to-top button
const CACHE_NAME = `kooptimizer-${CACHE_VERSION}`;
const ENABLE_CACHE = false; // Set to true for production, false for development

const urlsToCache = [
  '/',
  '/static/frontend/base.css',
  '/static/frontend/home.css',
  '/static/frontend/login.css',
  '/static/frontend/download.css',
  '/static/frontend/about.css',
  '/static/manifest.json'
];

self.addEventListener('install', event => {
  console.log('Service Worker installing with version:', CACHE_VERSION);
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
      .then(() => self.skipWaiting()) // Force the waiting service worker to become active
  );
});

self.addEventListener('activate', event => {
  console.log('Service Worker activating with version:', CACHE_VERSION);
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim()) // Take control of all pages immediately
  );
});

self.addEventListener('fetch', event => {
  // Skip cache if disabled (development mode)
  if (!ENABLE_CACHE) {
    return fetch(event.request);
  }
  
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache hit - return response from cache
        if (response) {
          // Also fetch from network to update cache in background
          fetch(event.request).then(networkResponse => {
            if (networkResponse && networkResponse.status === 200) {
              caches.open(CACHE_NAME).then(cache => {
                cache.put(event.request, networkResponse.clone());
              });
            }
          }).catch(() => {});
          return response;
        }
        
        // Not in cache - fetch from network
        return fetch(event.request).then(networkResponse => {
          // Don't cache if not a valid response
          if (!networkResponse || networkResponse.status !== 200 || networkResponse.type === 'error') {
            return networkResponse;
          }
          
          // Clone the response
          const responseToCache = networkResponse.clone();
          
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseToCache);
          });
          
          return networkResponse;
        });
      })
  );
});

