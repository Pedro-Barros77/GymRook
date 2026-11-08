/* Generated asset list: npm run build. All URLs stay within this application's scope. */
const VERSION = '340cfce2fc43d3df';
const ROOT = new URL('./', self.location.href);
// Include the scope in every cache name: GitHub Pages projects share an origin.
const PREFIX = 'gymrook-' + encodeURIComponent(ROOT.pathname) + '-';
const SHELL = PREFIX + 'shell-' + VERSION;
const MEDIA = PREFIX + 'media-' + VERSION;
const META = PREFIX + 'metadata-' + VERSION;
const url = relative => new URL(relative, ROOT).href;
const CORE = ['./', './index.html', './styles.css', './app.js', './data.js', './anatomy.js', './manifest.webmanifest', './asset-manifest.json', './assets/icons/icon-192.png', './assets/icons/icon-512.png', './assets/icons/apple-touch-icon.png'];
const marker = url('./__offline_ready__');
let downloading;

self.addEventListener('install', event => {
  // No skipWaiting here: an open page retains its matching cache and worker until closed.
  event.waitUntil(caches.open(SHELL).then(cache => cache.addAll(CORE.map(url))));
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const current = new Set([SHELL, MEDIA, META]);
    const names = await caches.keys();
    await Promise.all(names.filter(name => name.startsWith(PREFIX) && !current.has(name)).map(name => caches.delete(name)));
    await self.clients.claim();
  })());
});

async function send(client, message) {
  if (client) client.postMessage(message);
}

async function offlineReady() {
  const meta = await caches.open(META);
  if (!await meta.match(marker)) return false;
  const shell = await caches.open(SHELL);
  const media = await caches.open(MEDIA);
  const response = await shell.match(url('./asset-manifest.json')) || await media.match(url('./asset-manifest.json'));
  if (!response) { await meta.delete(marker); return false; }
  const manifest = await response.json();
  if (manifest.version !== VERSION) { await meta.delete(marker); return false; }
  for (const resource of [...new Set([...CORE, ...manifest.files])].map(url)) {
    if (!await shell.match(resource) && !await media.match(resource)) {
      await meta.delete(marker);
      return false;
    }
  }
  return true;
}

async function download(client) {
  const cache = await caches.open(MEDIA);
  const meta = await caches.open(META);
  // Clear the readiness marker until every file has been verified for this version.
  await meta.delete(marker);
  const manifestResponse = await fetch(url('./asset-manifest.json'), { cache: 'no-store' });
  if (!manifestResponse.ok) throw new Error('Não foi possível carregar a lista de arquivos.');
  const manifest = await manifestResponse.json();
  if (manifest.version !== VERSION) throw new Error('Há uma atualização disponível. Feche e abra o guia para baixar a versão atual.');
  const files = [...new Set([...CORE, ...manifest.files])].map(url);
  let done = 0;
  for (const resource of files) {
    if (new URL(resource).origin !== ROOT.origin || !new URL(resource).pathname.startsWith(ROOT.pathname)) throw new Error('Arquivo fora do guia.');
    const response = await fetch(resource, { cache: 'reload' });
    if (!response.ok) throw new Error('Um arquivo não pôde ser baixado. Tente novamente com conexão.');
    await cache.put(resource, response);
    await send(client, { type: 'OFFLINE_PROGRESS', done: ++done, total: files.length });
  }
  await meta.put(marker, new Response(VERSION));
  await send(client, { type: 'OFFLINE_READY', version: VERSION, done, total: files.length });
}

self.addEventListener('message', event => {
  if (event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting();
    return;
  }
  if (event.data?.type === 'CHECK_OFFLINE' || event.data?.type === 'GET_OFFLINE_STATUS') {
    event.waitUntil((async () => {
      const ready = await offlineReady();
      await send(event.source, { type: ready ? 'OFFLINE_READY' : 'OFFLINE_STATUS', ready: Boolean(ready), version: VERSION });
    })());
    return;
  }
  if (event.data?.type === 'DOWNLOAD_OFFLINE') {
    if (downloading) {
      send(event.source, { type: 'OFFLINE_ERROR', message: 'Já há um download em andamento. Aguarde a conclusão.' });
      return;
    }
    downloading = download(event.source).catch(error => send(event.source, { type: 'OFFLINE_ERROR', message: error.message || 'Não foi possível salvar o guia. Tente novamente.' })).finally(() => { downloading = null; });
    event.waitUntil(downloading);
  }
});

async function cachedResponse(request, cached) {
  const range = request.headers?.get('range');
  if (!range) return cached;
  // Mobile Safari requests byte ranges even for offline videos. A cached full
  // file must answer with a real 206, rather than ignoring the Range header.
  const bytes = await cached.arrayBuffer();
  const size = bytes.byteLength;
  const match = /^bytes=(\d*)-(\d*)$/.exec(range.trim());
  const headers = Object.fromEntries(cached.headers.entries());
  headers['Accept-Ranges'] = 'bytes';
  headers['Content-Type'] = cached.headers.get('content-type') || (request.url.endsWith('.mp4') ? 'video/mp4' : 'application/octet-stream');
  let start, end;
  if (match && (match[1] || match[2])) {
    if (!match[1]) {
      const suffix = Number(match[2]);
      start = Math.max(0, size - suffix);
      end = suffix > 0 ? size - 1 : -1;
    } else {
      start = Number(match[1]);
      end = match[2] ? Math.min(Number(match[2]), size - 1) : size - 1;
    }
  }
  if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start < 0 || start >= size || end < start) {
    headers['Content-Range'] = `bytes */${size}`;
    headers['Content-Length'] = '0';
    return new Response(null, { status: 416, headers });
  }
  headers['Content-Range'] = `bytes ${start}-${end}/${size}`;
  headers['Content-Length'] = String(end - start + 1);
  return new Response(bytes.slice(start, end + 1), { status: 206, headers });
}

self.addEventListener('fetch', event => {
  const request = event.request;
  const requested = new URL(request.url);
  if (request.method !== 'GET' || requested.origin !== ROOT.origin || !requested.pathname.startsWith(ROOT.pathname)) return;
  event.respondWith((async () => {
    const shell = await caches.open(SHELL);
    const media = await caches.open(MEDIA);
    const normalized = new Request(requested.origin + requested.pathname);
    const cached = await shell.match(request) || await media.match(request) || await shell.match(normalized) || await media.match(normalized);
    if (cached) return cachedResponse(request, cached);
    try {
      const response = await fetch(request);
      // Never replace a complete cached video with a partial network response.
      if (response.status === 200 && response.type === 'basic' && !requested.pathname.endsWith('/sw.js')) await media.put(request, response.clone());
      return response;
    } catch {
      if (request.mode === 'navigate') {
        const fallback = await shell.match(url('./index.html'));
        if (fallback) return fallback;
      }
      return new Response('Conteúdo ainda não disponível offline.', { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
    }
  })());
});
