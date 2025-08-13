const CACHE_NAME = 'ombra-tools-v4';
const STATIC_CACHE = 'ombra-static-v4';
const DYNAMIC_CACHE = 'ombra-dynamic-v4';

// Files to cache immediately
const STATIC_FILES = [
  '/',
  '/index.html',
  '/assets/styles/base.css',
  '/assets/scripts/effects.js',
  '/favicon.svg',
  '/favicon.ico',
  '/apple-touch-icon.png',
  // Tool pages
  '/tools/image-converter.html',
  '/tools/image-resizer.html',
  '/tools/pdf-to-text.html',
  '/tools/text-to-pdf.html',
  '/tools/pdf-merge.html',
  '/tools/image-to-pdf.html',
  '/tools/heic-to-jpg.html',
  '/tools/file-compressor.html',
  '/tools/color-converter.html',
  '/tools/calculator.html',
  '/tools/currency-converter.html',
  '/tools/ip-calculator.html',
  '/tools/ip-info.html',
  '/tools/whois-lookup.html',
  '/tools/dns-propagation.html',
  '/tools/dns-lookup.html',
  '/tools/unix-time.html',
  '/tools/uuid-generator.html',
  '/tools/text-diff.html',
  '/tools/json-to-csv.html',
  '/tools/text-statistics.html',
  '/tools/lorem-ipsum.html',
  '/tools/number-converter.html',
  '/tools/password-generator.html',
  '/tools/hash-generator.html'
];

// Install event - cache static files
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('Caching static files for offline use');
        return cache.addAll(STATIC_FILES);
      })
      .catch(error => {
        console.log('Some files failed to cache:', error);
      })
  );
  
  // Force activation immediately
  self.skipWaiting();
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

// Fetch event - serve from cache when offline
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

  event.respondWith(
    // Try network first, then cache
    fetch(request)
      .then(response => {
        // Don't cache non-successful responses
        if (!response || response.status !== 200 || response.type !== 'basic') {
          return response;
        }

        // Clone the response for caching
        const responseToCache = response.clone();

        // Cache successful responses
        caches.open(DYNAMIC_CACHE)
          .then(cache => {
            cache.put(request, responseToCache);
          });

        return response;
      })
      .catch(() => {
        // If offline, try cache
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
      })
  );
});

// Message handling for cache updates
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
