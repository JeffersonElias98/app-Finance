const CACHE_NAME = 'money-app-v99'; 

const assets = [
  './',
  './index.html',
  './investimentos.html',
  './logo.png',
  './icon-512.png',
  'https://cdn.jsdelivr.net/npm/chart.js',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

self.addEventListener('install', event => {
  self.skipWaiting(); 
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(assets))
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      );
    })
  );
  return self.clients.claim(); // Controla a página imediatamente
});

self.addEventListener('fetch', event => {
  const req = event.request;
  const url = new URL(req.url);

  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then(networkResponse => {
          return caches.open(CACHE_NAME).then(cache => {
            cache.put(req, networkResponse.clone()); // Atualiza o cache com a versão nova
            return networkResponse;
          });
        })
        .catch(() => caches.match(req)) // Se estiver offline, usa o cache
    );
    return;
  }
  
  event.respondWith(
    caches.match(req).then(cachedResponse => {
      return cachedResponse || fetch(req).then(networkResponse => {
        return caches.open(CACHE_NAME).then(cache => {
          cache.put(req, networkResponse.clone());
          return networkResponse;
        });
      });
    })
  );
});
