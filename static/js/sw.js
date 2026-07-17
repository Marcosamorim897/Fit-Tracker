/* Service worker do FitTracker.
 *
 * Estratégia conservadora, pensada para um app com dados por usuário:
 *  - assets estáticos (css/js/ícones): cache-first, com cache versionado;
 *  - navegações (HTML): sempre rede, com página offline como fallback —
 *    nunca servimos do cache uma página autenticada possivelmente velha.
 */

const CACHE = "fittracker-v1";
const PRECACHE = [
  "/static/css/style.css",
  "/static/js/progress.js",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
  "/static/offline.html",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  // páginas: rede primeiro; se estiver sem conexão, mostra a página offline
  if (req.mode === "navigate") {
    event.respondWith(fetch(req).catch(() => caches.match("/static/offline.html")));
    return;
  }

  // assets estáticos: cache primeiro, buscando na rede só quando faltar
  const url = new URL(req.url);
  if (url.origin === location.origin && url.pathname.startsWith("/static/")) {
    event.respondWith(
      caches.match(req).then(
        (hit) =>
          hit ||
          fetch(req).then((resp) => {
            const copia = resp.clone();
            caches.open(CACHE).then((cache) => cache.put(req, copia));
            return resp;
          })
      )
    );
  }
});
