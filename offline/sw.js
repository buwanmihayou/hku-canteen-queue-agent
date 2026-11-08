/* Generated sw.js versions the cache from the complete offline asset set. */
"use strict";
const CACHE = "hku-canteen-offline-71237a2c0033dca3";
const SCOPE = self.registration.scope;
const ASSETS = ["./", "./index.html", "./offline.html", "./data.json", "./manifest.webmanifest", "./icon-192.png", "./icon-512.png"];
self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith("hku-canteen-offline-") && key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", event => {
  const request = event.request;
  if (request.method !== "GET" || !request.url.startsWith(SCOPE)) return;
  event.respondWith(caches.open(CACHE).then(async cache => {
    const cached = await cache.match(request, {ignoreSearch: true});
    if (cached) return cached;
    try { return await fetch(request); }
    catch (error) {
      if (request.mode === "navigate") return cache.match(new URL("./index.html", SCOPE).href);
      throw error;
    }
  }));
});
