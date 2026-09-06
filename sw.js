/* Service worker — pozwala uruchomić aplikację bez internetu.
   Po zmianie plików podnieś numer wersji, żeby telefon pobrał nowe. */
const CACHE = "autobus-v24";
const FILES = [
  "./",
  "./index.html",
  "./marysia.html",
  "./janek.html",
  "./alicja.html",
  "./autobus.css",
  "./autobus.js",
  "./manifest-marysia.webmanifest",
  "./manifest-janek.webmanifest",
  "./manifest-alicja.webmanifest",
  "./icon-180.png",
  "./icon-192.png",
  "./icon-512.png",
  "./icon-janek-180.png",
  "./icon-janek-192.png",
  "./icon-janek-512.png",
  "./icon-alicja-180.png",
  "./icon-alicja-192.png",
  "./icon-alicja-512.png"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(FILES))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

/* Najpierw sieć (żeby aktualizacje wchodziły od razu), a gdy jej brak — cache.
   Zapasowo oddajemy stronę dziecka pasującą do adresu, nie zawsze index. */
self.addEventListener("fetch", event => {
  if (event.request.method !== "GET") return;
  event.respondWith(
    fetch(event.request)
      .then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(event.request, copy)).catch(() => {});
        return res;
      })
      .catch(() => caches.match(event.request).then(hit => {
        if (hit) return hit;
        const url = new URL(event.request.url);
        const zapas = url.pathname.includes("janek") ? "./janek.html"
                    : url.pathname.includes("alicja") ? "./alicja.html"
                    : url.pathname.includes("marysia") ? "./marysia.html"
                    : "./index.html";
        return caches.match(zapas);
      }))
  );
});
