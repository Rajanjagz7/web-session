/* Service worker: shows push notifications (also when the app is closed) and handles taps. */
const SHELL = 'algo-shell-v38';

const UPDATING_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Updating · Rajan Algo</title>
<style>
  :root { color-scheme: dark; }
  body { background:#0B0E14; color:#E6EAF2; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,sans-serif; margin:0; min-height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; padding:24px; box-sizing:border-box; }
  .box { background:#11151D; border:1px solid #232A37; border-radius:16px; padding:32px 24px; max-width:380px; width:100%; box-shadow:0 12px 36px rgba(0,0,0,.5); }
  .spinner { width:38px; height:38px; border:3px solid rgba(57,135,229,.2); border-top-color:#3987e5; border-radius:50%; animation:spin 0.8s linear infinite; margin:0 auto 20px; }
  @keyframes spin { to { transform:rotate(360deg); } }
  h2 { font-size:18px; font-weight:700; margin:0 0 10px; color:#fff; }
  p { font-size:13.5px; color:#A3ADBF; margin:0 0 18px; line-height:1.5; }
  .retry-btn { background:#3987e5; color:#fff; border:0; border-radius:8px; padding:9px 18px; font-size:13px; font-weight:600; cursor:pointer; font-family:inherit; }
  .dots { display:inline-block; animation:pulse 1.4s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
</style>
<script>
  let tries = 0;
  function probe() {
    tries++;
    fetch('/', { cache: 'no-store' }).then(r => {
      if (r.ok && r.status < 400) { location.reload(); }
      else if (tries < 20) { setTimeout(probe, 2000); }
    }).catch(() => {
      if (tries < 20) { setTimeout(probe, 2000); }
    });
  }
  setTimeout(probe, 1500);
</script>
</head>
<body>
<div class="box">
  <div class="spinner"></div>
  <h2>Updating to latest version<span class="dots">…</span></h2>
  <p>A new release is being applied. The app will refresh automatically in a few seconds.</p>
  <button class="retry-btn" onclick="location.reload()">Refresh now</button>
</div>
</body>
</html>`;

self.addEventListener('install', e => {
  e.waitUntil(caches.open(SHELL).then(c => c.addAll(['/', '/static/journal.js', '/manifest.webmanifest', '/favicon.svg', '/icon-192.png'])).catch(() => {}));
  self.skipWaiting();
});

self.addEventListener('fetch', e => {
  const r = e.request, u = new URL(r.url);
  if (r.method !== 'GET' || u.origin !== location.origin || u.pathname.startsWith('/api/')) return;
  if (!(r.mode === 'navigate' || u.pathname === '/' || u.pathname.startsWith('/static/') || u.pathname.endsWith('.webmanifest') || u.pathname.endsWith('.svg') || u.pathname.endsWith('.png'))) return;
  e.respondWith((async () => {
    try {
      const res = await fetch(r);
      if (res && res.ok) {
        const copy = res.clone();
        caches.open(SHELL).then(c => c.put(r, copy)).catch(() => {});
        return res;
      }
      // If server returned 404 or 5xx (e.g. during deployment swap or asset migration)
      if (res && (res.status === 404 || res.status >= 500)) {
        if (r.mode === 'navigate') {
          const cachedHome = await caches.match('/', { ignoreSearch: true });
          if (cachedHome) return cachedHome;
          return new Response(UPDATING_HTML, { headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' } });
        }
        const cachedAsset = await caches.match(r, { ignoreSearch: true });
        if (cachedAsset) return cachedAsset;
      }
      return res;
    } catch (_) {
      const m = await caches.match(r, { ignoreSearch: true });
      if (m) return m;
      if (r.mode === 'navigate') {
        const home = await caches.match('/', { ignoreSearch: true });
        if (home) return home;
        return new Response(UPDATING_HTML, { headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' } });
      }
      throw _;
    }
  })());
});

self.addEventListener('activate', e => e.waitUntil((async () => {
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
