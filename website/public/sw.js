/* AegisOS V8: service-worker page caching intentionally disabled.
   Next.js immutable hashed assets + route prefetching provide safe caching
   without allowing stale interface bundles to mask new deployments. */
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(key => key.startsWith("aegisos-")).map(key => caches.delete(key)));
    await self.registration.unregister();
    await self.clients.claim();
  })());
});
