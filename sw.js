const CACHE_NAME = 'ombra-tools-v68';
const STATIC_CACHE = 'ombra-static-v68';
const DYNAMIC_CACHE = 'ombra-dynamic-v68';
const MAX_CACHE_SIZE = 50; // Maximum number of items in dynamic cache

// Only cache critical files immediately for faster initial load
const CRITICAL_FILES = [
  '/',
  '/index.html',
  '/assets/styles/base.css',
  '/assets/scripts/effects.js',
  '/assets/scripts/settings.js',
  '/assets/scripts/visitor-counter.js',
  '/favicon.svg'
];

// Install event - cache only critical files
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('Caching critical files for offline use');
        return cache.addAll(CRITICAL_FILES);
      })
      .catch(error => {
        console.log('Some files failed to cache:', error);
      })
  );
});

// Activate event - clean up old caches and take control immediately
self.addEventListener('activate', event => {
  event.waitUntil(
    Promise.all([
      // Take control of all clients immediately
      self.clients.claim(),
      
      // Clean up old caches
      caches.keys().then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              console.log('Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
    ])
  );
});

// Helper function to limit cache size
async function limitCacheSize(cacheName, maxSize) {
  const cache = await caches.open(cacheName);
  const keys = await cache.keys();
  if (keys.length > maxSize) {
    // Delete oldest entries (simple FIFO)
    const toDelete = keys.slice(0, keys.length - maxSize);
    await Promise.all(toDelete.map(key => cache.delete(key)));
  }
}

// Fetch event - serve from cache when offline, lazy cache tool pages
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle GET requests and same-origin requests
  if (request.method !== 'GET' || !url.origin.startsWith(self.location.origin)) {
    return;
  }

  // Skip caching for dynamic content or API calls
  if (request.url.includes('?') || request.url.includes('api')) {
    return;
  }

  // Check if it's a tool page (lazy cache)
  const isToolPage = url.pathname.startsWith('/tools/');

  event.respondWith(
    // Try cache first for tool pages (lazy cached), network first for others
    (isToolPage ? caches.match(request) : Promise.resolve(null))
      .then(cachedResponse => {
        if (cachedResponse) {
          return cachedResponse;
        }
        
        // Try network
        return fetch(request)
          .then(response => {
            // Don't cache non-successful responses
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // Lazy cache tool pages and other resources
            if (isToolPage || url.pathname.startsWith('/assets/')) {
              const responseToCache = response.clone();
              caches.open(DYNAMIC_CACHE)
                .then(cache => {
                  cache.put(request, responseToCache);
                  // Limit cache size
                  limitCacheSize(DYNAMIC_CACHE, MAX_CACHE_SIZE);
                });
            }

            return response;
          })
          .catch(() => {
            // If offline, try cache (fallback)
            return caches.match(request)
              .then(cachedResponse => {
                if (cachedResponse) {
                  return cachedResponse;
                }
                // If no cache and offline, return offline page for documents
                if (request.destination === 'document') {
                  return caches.match('/index.html');
                }
              });
          });
      })
  );
});

// Message handling for cache updates
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
