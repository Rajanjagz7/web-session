/* Service worker: shows push notifications (also when the app is closed) and handles taps. */
const SHELL = 'algo-shell-v10';
self.addEventListener('install', e => {
  e.waitUntil(caches.open(SHELL).then(c => c.addAll(['/', '/static/journal.js', '/manifest.webmanifest', '/favicon.svg', '/icon-192.png'])).catch(() => {}));
  self.skipWaiting();
});
/* Network first (so a phone never runs a stale build); the cached shell is only used when the network is unreachable. */
self.addEventListener('fetch', e => {
  const r = e.request, u = new URL(r.url);
  if (r.method !== 'GET' || u.origin !== location.origin || u.pathname.startsWith('/api/')) return;
  if (!(r.mode === 'navigate' || u.pathname === '/' || u.pathname.startsWith('/static/') || u.pathname.endsWith('.webmanifest') || u.pathname.endsWith('.svg') || u.pathname.endsWith('.png'))) return;
  e.respondWith(fetch(r).then(res => {
    if (res && res.ok) { const copy = res.clone(); caches.open(SHELL).then(c => c.put(r, copy)).catch(() => {}); }
    return res;
  }).catch(() => caches.match(r, { ignoreSearch: true }).then(m => m || caches.match('/'))));
});
self.addEventListener('activate', e => e.waitUntil((async () => {   // shell bump: drop every older cache so devices start clean
  const names = await caches.keys();
  await Promise.all(names.filter(n => n !== SHELL).map(n => caches.delete(n)));
  await self.clients.claim();
})()));

self.addEventListener('push', e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (_) { d = { title: 'Notification', body: e.data ? e.data.text() : '' }; }
  const title = d.title || 'Rajan Algo';
  e.waitUntil(self.registration.showNotification(title, {
    body: d.body || '',
    tag: d.tag || undefined,
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    data: { url: d.url || '/', nid: d.nid || null },
    requireInteraction: !!d.critical
  }));
});

self.addEventListener('notificationclick', e => {
  e.notification.close();
  const data = e.notification.data || {};
  e.waitUntil((async () => {
    const all = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const c of all) {
      if ('focus' in c) { await c.focus(); c.postMessage({ type: 'rn-open', nid: data.nid, url: data.url }); return; }
    }
    if (self.clients.openWindow) await self.clients.openWindow(data.url || '/');
  })());
});
