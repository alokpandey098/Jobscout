const V = "jobscout-v1";
self.addEventListener("install", e => {
  e.waitUntil(caches.open(V).then(c => c.addAll(["./", "manifest.webmanifest", "icons/icon-192.png"])).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const r = e.request;
  if (r.method !== "GET") return;
  const u = new URL(r.url);
  if (u.origin !== location.origin) return;
  const keep = x => { if (x.ok) { const c = x.clone(); caches.open(V).then(ca => ca.put(r, c)); } return x; };
  if (u.pathname.includes("/vendor/")) {            // big, never changes: cache first
    e.respondWith(caches.match(r).then(m => m || fetch(r).then(keep)));
    return;
  }
  e.respondWith(fetch(r).then(keep).catch(() => caches.match(r).then(m => m || caches.match("./"))));  // network first, offline fallback
});
