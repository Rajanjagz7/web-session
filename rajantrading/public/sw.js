/* Service worker: shows push notifications (also when the app is closed) and handles taps. */
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));

self.addEventListener('push', e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (_) { d = { title: 'Notification', body: e.data ? e.data.text() : '' }; }
  const title = d.title || 'Algo Trades';
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
