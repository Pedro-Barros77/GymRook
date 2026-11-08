import assert from 'node:assert/strict';
import { readFile, readdir, stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import crypto from 'node:crypto';
import vm from 'node:vm';
import { checkUI } from './check-ui.mjs';

const root = fileURLToPath(new URL('../dist/', import.meta.url));
const read = file => readFile(path.join(root, file));
const text = async file => (await read(file)).toString('utf8');
const fail = message => { throw new Error(message); };
const nonempty = value => typeof value === 'string' && value.trim().length > 0;
const stringList = value => Array.isArray(value) && value.length > 0 && value.every(nonempty);
const legMotionIds = ['leg-extension', 'hack-squat', 'lying-leg-curl', 'dumbbell-stiff-leg-deadlift', 'machine-hip-abduction', 'machine-hip-adduction', 'alternating-lunge'];
const bcMotionIds = ['machine-shoulder-press', 'dumbbell-lateral-raise', 'cable-front-raise', 'dumbbell-shrug', 'reverse-pec-deck', 'standing-machine-calf-raise', 'seated-plate-calf-raise', 'lat-pulldown', 'unilateral-cable-row', 'seated-cable-row', 'rope-triceps-pushdown', 'dumbbell-lying-triceps-extension', 'bench-dip', 'machine-ab-crunch'];
const aMotionIds = ['incline-dumbbell-press', 'high-cable-crossover', 'pec-deck', 'push-up', 'cable-biceps-curl', 'preacher-curl', 'reverse-cable-curl', 'floor-crunch', 'lying-leg-raise', 'forearm-plank'];
const pilotIds = [...aMotionIds, ...legMotionIds, ...bcMotionIds];
const revisedIds = new Set([...aMotionIds, 'lying-leg-curl', 'dumbbell-stiff-leg-deadlift', 'alternating-lunge', 'dumbbell-lateral-raise', 'reverse-pec-deck', 'seated-plate-calf-raise', 'unilateral-cable-row', 'machine-ab-crunch']);
const repairedIds = new Set(['preacher-curl', 'reverse-pec-deck', 'seated-plate-calf-raise', 'machine-ab-crunch', 'leg-extension', 'hack-squat', 'lying-leg-curl', 'dumbbell-stiff-leg-deadlift', 'alternating-lunge']);
const followupIds = new Set(['preacher-curl', 'lying-leg-raise', 'standing-machine-calf-raise', 'machine-ab-crunch']);
async function walk(directory = root) {
  const result = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) result.push(...await walk(absolute));
    else if (entry.isFile()) result.push(path.relative(root, absolute).split(path.sep).join('/'));
  }
  return result;
}
function safePath(resource) {
  assert(nonempty(resource), 'Empty asset path');
  const url = new URL(resource, 'https://example.test/GymRook/');
  assert.equal(url.origin, 'https://example.test', `External asset: ${resource}`);
  assert(url.pathname.startsWith('/GymRook/'), `Asset escapes project scope: ${resource}`);
  assert(!url.search && !url.hash, `Unexpected query/hash in asset: ${resource}`);
  return decodeURIComponent(url.pathname.slice('/GymRook/'.length)) || 'index.html';
}
async function exists(resource) {
  const file = safePath(resource);
  assert((await stat(path.join(root, file))).isFile(), `Missing asset: ${resource}`);
  return file;
}
// Count image descriptors by walking GIF blocks, rather than searching compressed bytes.
function gifFrames(bytes, file) {
  assert(bytes.length >= 14 && ['GIF87a', 'GIF89a'].includes(bytes.subarray(0, 6).toString('ascii')), `Invalid GIF header: ${file}`);
  let p = 13;
  if (bytes[10] & 0x80) p += 3 * (2 ** ((bytes[10] & 7) + 1));
  let frames = 0, trailer = false;
  function subBlocks() {
    while (true) {
      assert(p < bytes.length, `Truncated GIF: ${file}`);
      const size = bytes[p++];
      if (!size) return;
      p += size;
      assert(p <= bytes.length, `Truncated GIF data: ${file}`);
    }
  }
  while (p < bytes.length) {
    const marker = bytes[p++];
    if (marker === 0x3b) { trailer = true; break; }
    if (marker === 0x21) { assert(p < bytes.length, `Truncated GIF extension: ${file}`); p++; subBlocks(); continue; }
    assert.equal(marker, 0x2c, `Invalid GIF block in ${file}`);
    assert(p + 9 <= bytes.length, `Truncated GIF image: ${file}`);
    const packed = bytes[p + 8]; p += 9;
    if (packed & 0x80) p += 3 * (2 ** ((packed & 7) + 1));
    assert(p < bytes.length, `Truncated GIF image data: ${file}`);
    p++; subBlocks(); frames++;
  }
  assert(trailer, `Missing GIF trailer: ${file}`);
  return frames;
}

async function checkVideoMedia(id, media, renderManifests) {
  assert(pilotIds.includes(id), `${id}: unexpected motion video`);
  const fps = 12;
  const frames = id === 'alternating-lunge' ? 72 : 36;
  const duration = frames / fps;
  assert(['generated-static-hold', 'generated-interpolated'].includes(media.render), `${id}: video must identify its rendering/interpolation source`);
  assert.equal(media.fps, fps, `${id}: motion video has the wrong frame rate`);
  assert.equal(media.frameCount, frames, `${id}: motion cycle has the wrong frame count`);
  const directory = followupIds.has(id) ? 'animations-v4' : repairedIds.has(id) ? 'animations-v3' : revisedIds.has(id) ? 'animations-v2' : legMotionIds.includes(id) ? 'animations-d-v1' : 'animations-bc-v1';
  const mediaId = id;
  assert.equal(media.video, `assets/${directory}/${mediaId}.mp4`, `${id}: incorrect video path`);
  assert.equal(media.gif, `assets/${directory}/${mediaId}.gif`, `${id}: incorrect GIF path`);
  assert.equal(media.poster, `assets/${directory}/${mediaId}-poster.webp`, `${id}: incorrect poster path`);
  const video = await exists(media.video);
  const gif = await exists(media.gif);
  const poster = await exists(media.poster);
  assert(video.toLowerCase().endsWith('.mp4'), `${id}: preferred motion video must be MP4`);
  assert.equal((await read(video)).subarray(4, 8).toString('ascii'), 'ftyp', `${id}: invalid MP4 file header`);
  const manifestPath = path.posix.join(path.posix.dirname(video), 'manifest.json');
  if (!renderManifests.has(manifestPath)) renderManifests.set(manifestPath, JSON.parse(await text(manifestPath)));
  const renders = renderManifests.get(manifestPath);
  assert.equal(renders.preferredFormat, 'MP4', `${id}: motion manifest must prefer MP4`);
  assert.equal(renders.fps, fps, `${id}: motion manifest has the wrong frame rate`);
  const record = renders.animations.find(animation => animation.id === mediaId);
  assert(record, `${id}: missing motion record`);
  assert.equal(record.frameCount, frames, `${id}: manifest has the wrong frame count`);
  assert.equal(record.fps, fps, `${id}: manifest has the wrong frame rate`);
  assert.equal(record.durationSeconds, duration, `${id}: manifest has the wrong cycle duration`);
  const actualGifFrames = gifFrames(await read(gif), gif);
  assert(actualGifFrames >= (media.isometric ? 1 : 2), `${id}: compatibility GIF must contain the required frames`);
  assert.equal(actualGifFrames, record.gifFrames, `${id}: compatibility GIF count differs from its manifest`);
  if (media.isometric) assert.equal(actualGifFrames, 1, `${id}: isometric demonstration must preserve a stable posture`);
  else if (id === 'alternating-lunge') assert(actualGifFrames <= frames, `${id}: too many compatibility GIF frames`);
  else assert.equal(actualGifFrames, frames, `${id}: compatibility GIF has the wrong frame count`);
  assert.equal(record.gifDurationMilliseconds, duration * 1000, `${id}: compatibility GIF has the wrong duration`);
  for (const [file, filename] of [[video, record.video], [gif, record.gif], [poster, record.poster]]) {
    assert.equal(path.posix.basename(file), filename, `${id}: manifest references the wrong media file`);
    const expected = record.files[filename];
    assert(expected, `${id}: missing integrity record for ${filename}`);
    const content = await read(file);
    assert.equal(content.length, expected.bytes, `${id}: media byte count differs from its record`);
    assert.equal(crypto.createHash('sha256').update(content).digest('hex'), expected.sha256, `${id}: media hash differs from its record`);
  }
}

async function checkStatic() {
  const context = { window: {} };
  vm.runInNewContext(await text('data.js'), context, { filename: 'data.js', timeout: 1000 });
  const data = context.window.GYMROOK_DATA;
  assert(data && Array.isArray(data.workouts) && data.exercises, 'data.js must expose workouts and exercises');
  assert.equal(data.workouts.length, 4, 'Expected four workouts');
  const ids = Object.keys(data.exercises);
  assert.equal(ids.length, 31, 'Expected 31 exercises');
  const assigned = new Set();
  assert.deepEqual(data.workouts.map(w => w.id).sort().join(','), 'A,B,C,D', 'Expected workouts A through D');
  for (const workout of data.workouts) {
    for (const key of ['id', 'name', 'subtitle']) assert(nonempty(workout[key]), `Workout missing ${key}`);
    assert(Array.isArray(workout.blocks) && workout.blocks.length, `Workout ${workout.id} has no blocks`);
    for (const block of workout.blocks) {
      assert(nonempty(block.title) && nonempty(block.prescription) && stringList(block.exerciseIds), `Invalid block in ${workout.id}`);
      for (const id of block.exerciseIds) {
        assert(data.exercises[id], `Block references unknown exercise ${id}`);
        assigned.add(id);
      }
    }
  }
  assert.equal(assigned.size, ids.length, 'Some exercises are not assigned to a workout');
  assert.notEqual(data.exercises['floor-crunch'].media.video, data.exercises['lying-leg-raise'].media.video, 'Supra and infra must demonstrate different movements');
  const pilots = [];
  const renderManifests = new Map();
  for (const [id, exercise] of Object.entries(data.exercises)) {
    for (const key of ['name', 'nameEn', 'equipment', 'equipmentEn']) assert(nonempty(exercise[key]), `${id}: missing ${key}`);
    for (const key of ['primary', 'muscleIds', 'setup', 'steps', 'cues', 'mistakes']) assert(stringList(exercise[key]), `${id}: missing ${key}`);
    assert(Array.isArray(exercise.secondary) && exercise.secondary.every(nonempty), `${id}: invalid secondary muscles`);
    const thumbnail = await exists(exercise.media?.poster || exercise.thumbnail || `assets/thumbnails/${id}.webp`);
    assert((await read(thumbnail)).length > 0, `${id}: empty representative image`);
    if (exercise.pilot) pilots.push(id);
    if (exercise.media) {
      assert(exercise.pilot, `${id}: media should identify a pilot`);
      if (pilotIds.includes(id)) {
        assert(exercise.media.video, `${id}: expected a motion video`);
        assert.equal(exercise.media.render, id === 'forearm-plank' ? 'generated-static-hold' : 'generated-interpolated', `${id}: expected generated illustration with correct motion or hold type`);
        assert(!exercise.media.experimental && !exercise.media.legacy, `${id}: unexpected comparison version`);
      }
      const poster = await exists(exercise.media.poster);
      const gif = await exists(exercise.media.gif);
      assert(gif.toLowerCase().endsWith('.gif'), `${id}: animation must be a GIF`);
      const actualGifFrames = gifFrames(await read(gif), gif);
      if (exercise.media.video) {
        await checkVideoMedia(id, exercise.media, renderManifests);
      } else {
        assert.equal(actualGifFrames, 16, `${id}: legacy 2D GIF must contain exactly 16 frames`);
      }
      if (exercise.media.experimental) {
        assert.equal(exercise.media.experimental.render, 'generated-interpolated', `${id}: optional experiment must identify interpolation, not a 3D scene`);
        assert(!exercise.media.video, `${id}: original GIF must remain the default when an experiment is offered`);
        await checkVideoMedia(id, exercise.media.experimental, renderManifests);
      }
      if (exercise.media.legacy) {
        const legacyGif = await exists(exercise.media.legacy.gif);
        await exists(exercise.media.legacy.poster);
        const legacyFrameCount = exercise.media.legacy.frameCount ?? 16;
        assert(Number.isSafeInteger(legacyFrameCount) && legacyFrameCount > 0, `${id}: legacy frame count must be a positive integer`);
        assert.equal(gifFrames(await read(legacyGif), legacyGif), legacyFrameCount, `${id}: preserved GIF frame count differs from its declared value`);
      }
      assert((await read(poster)).length > 0, `${id}: empty poster`);
    } else assert(!exercise.pilot, `${id}: pilot is missing media`);
  }
  assert.deepEqual(pilots.sort(), [...pilotIds].sort(), 'Visual pilot exercises do not match the prescribed set');
  assert(data.exercises['pec-deck'].media?.video, 'Pec deck must preserve its primary video');
  assert(!data.exercises['stair-calf-raise'] && !data.exercises['unilateral-converging-row'], 'Replaced exercises must not remain in the active guide');
  assert(data.exercises['seated-plate-calf-raise'].primary.includes('Sóleo'), 'Seated calf raise must emphasize soleus');
  assert(data.exercises['forearm-plank'].media.isometric, 'Plank must identify its isometric hold');
  const manifest = JSON.parse(await text('manifest.webmanifest'));
  assert.equal(manifest.start_url, './', 'PWA start_url must be scope-relative');
  assert.equal(manifest.scope, './', 'PWA scope must be relative');
  assert.equal(manifest.id, './', 'PWA id must be scope-relative');
  assert(Array.isArray(manifest.icons) && manifest.icons.length, 'Manifest has no icons');
  for (const icon of manifest.icons) await exists(icon.src);
  const html = await text('index.html');
  for (const match of html.matchAll(/(?:src|href)=["']([^"'#]+)["']/g)) {
    if (!/^(?:https?:|mailto:|data:)/i.test(match[1])) await exists(match[1]);
  }
  const generated = JSON.parse(await text('asset-manifest.json'));
  assert(/^[a-f0-9]{16}$/.test(generated.version), 'Invalid asset manifest version');
  assert(Array.isArray(generated.files) && generated.files.every(f => f.startsWith('./')), 'Invalid asset manifest files');
  const actual = (await walk()).filter(f => !['sw.js', 'asset-manifest.json', '.nojekyll'].includes(f)).sort();
  const listed = generated.files.map(safePath).sort();
  assert.deepEqual(listed, actual, 'Asset manifest does not match dist files; run npm run build');
  const hash = crypto.createHash('sha256');
  const worker = await text('sw.js');
  hash.update('sw.js').update(worker.replace(/const VERSION = '[^']+';/, "const VERSION = 'release';"));
  let bytes = 0;
  for (const file of actual) { const content = await read(file); hash.update(file).update(content); bytes += content.length; }
  assert.equal(generated.version, hash.digest('hex').slice(0, 16), 'Asset manifest version is stale; run npm run build');
  assert.equal(generated.bytes, bytes, 'Asset manifest byte count is stale');
  assert((await text('sw.js')).includes(`const VERSION = '${generated.version}';`), 'Service worker version does not match manifest');
  console.log(`Static assets: ${ids.length} exercises, ${pilots.length} animated pilots, ${actual.length} versioned files.`);
  const video = Object.values(data.exercises).map(exercise => exercise.media?.video || exercise.media?.experimental?.video).find(Boolean) || null;
  return { generated, gif: data.exercises[pilots[0]].media.gif, video };
}

async function workerHarness(manifest, options = {}) {
  const scope = 'https://example.test/GymRook/';
  const stores = new Map(), listeners = {}, requests = [];
  let offline = false;
  const key = request => typeof request === 'string' ? new URL(request, scope).href : request.url;
  const fetchFile = async request => {
    const url = key(request); requests.push(url);
    if (offline) throw new TypeError('Network unavailable');
    if (options.fail && url.endsWith(options.fail)) return new Response('missing', { status: 404 });
    if (options.wrongVersion && url.endsWith('/asset-manifest.json')) return Response.json({ ...manifest, version: 'old-version' });
    try { return new Response(await read(safePath(url))); }
    catch { return new Response('missing', { status: 404 }); }
  };
  const caches = {
    async open(name) {
      if (!stores.has(name)) stores.set(name, new Map());
      const store = stores.get(name);
      // Cache Storage persists bytes, not a live tee of a fetch body stream.
      // Independent responses on each match also exercise repeated video reads.
      const persist = async (request, response) => {
        store.set(key(request), {
          bytes: new Uint8Array(await response.arrayBuffer()),
          status: response.status,
          headers: [...response.headers.entries()]
        });
      };
      return {
        async addAll(urls) { for (const url of urls) { const response = await fetchFile(url); if (!response.ok) throw Error(`Cannot cache ${url}`); await persist(url, response); } },
        async put(request, response) { await persist(request, response); },
        async match(request) {
          const stored = store.get(key(request));
          return stored && new Response(stored.bytes.slice(), { status: stored.status, headers: stored.headers });
        },
        async delete(request) { return store.delete(key(request)); }
      };
    },
    async keys() { return [...stores.keys()]; },
    async delete(name) { return stores.delete(name); }
  };
  const self = { location: { href: scope + 'sw.js' }, clients: { async claim() {} }, skipWaiting() {}, addEventListener(type, handler) { listeners[type] = handler; } };
  vm.runInNewContext(await text('sw.js'), { self, caches, fetch: fetchFile, URL, Request, Response, console }, { filename: 'sw.js', timeout: 1000 });
  async function event(type, properties = {}) {
    const pending = [];
    let response;
    listeners[type]({ ...properties, waitUntil(promise) { pending.push(promise); }, respondWith(promise) { response = promise; } });
    await Promise.all(pending);
    return response && await response;
  }
  async function message(type) { const messages = []; await event('message', { data: { type }, source: { postMessage(m) { messages.push(m); } } }); return messages; }
  return { scope, stores, caches, requests, event, message, setOffline(value) { offline = value; }, setFailure(value) { options.fail = value; } };
}
async function checkWorker(manifest, gif, video) {
  const h = await workerHarness(manifest);
  await h.caches.open('gymrook-%2FGymRook%2F-shell-obsolete');
  await h.caches.open('gymrook-%2Fsibling%2F-shell-obsolete');
  await h.event('install'); await h.event('activate');
  assert(!h.stores.has('gymrook-%2FGymRook%2F-shell-obsolete'), 'Old cache for this scope was not cleaned up');
  assert(h.stores.has('gymrook-%2Fsibling%2F-shell-obsolete'), 'Activation removed a sibling project cache');
  assert.equal((await h.message('CHECK_OFFLINE'))[0].type, 'OFFLINE_STATUS', 'Install alone should not mark full download ready');
  h.requests.length = 0;
  const messages = await h.message('DOWNLOAD_OFFLINE');
  const ready = messages.find(m => m.type === 'OFFLINE_READY');
  assert(ready && messages.at(-1) === ready, 'Full download did not finish with OFFLINE_READY');
  const progress = messages.filter(m => m.type === 'OFFLINE_PROGRESS');
  assert.equal(progress.length, ready.total, 'Missing progress events');
  assert.equal(ready.done, ready.total, 'Ready was reported before completion');
  const expected = new Set(['./', './index.html', './styles.css', './app.js', './anatomy.js', './data.js', './manifest.webmanifest', './asset-manifest.json', './assets/icons/icon-192.png', './assets/icons/icon-512.png', './assets/icons/apple-touch-icon.png', ...manifest.files].map(f => new URL(f, h.scope).href));
  assert.equal(ready.total, expected.size, 'Download did not include every asset');
  for (const url of expected) {
    const count = h.requests.filter(request => request === url).length;
    assert.equal(count, url.endsWith('/asset-manifest.json') ? 2 : 1, `Unexpected number of download requests for ${url}`);
  }
  assert.equal((await h.message('CHECK_OFFLINE'))[0].type, 'OFFLINE_READY', 'Downloaded content did not persist as ready');
  // Simulate partial browser storage eviction after a successful download.
  const gifUrl = new URL(gif, h.scope).href;
  for (const store of h.stores.values()) store.delete(gifUrl);
  assert.equal((await h.message('CHECK_OFFLINE'))[0].type, 'OFFLINE_STATUS', 'An evicted asset must invalidate offline readiness');
  assert((await h.message('DOWNLOAD_OFFLINE')).some(m => m.type === 'OFFLINE_READY'), 'Download could not repair an evicted asset');
  h.setOffline(true);
  const navigation = await h.event('fetch', { request: { url: h.scope + 'missing-route', method: 'GET', mode: 'navigate' } });
  assert.equal(navigation.status, 200, 'Offline navigation fallback failed');
  assert.equal(await navigation.text(), await text('index.html'), 'Offline navigation must return the app shell');
  const image = await h.event('fetch', { request: new Request(new URL(gif, h.scope)) });
  assert.equal(image.status, 200, 'Downloaded animation unavailable offline');
  assert.equal(Buffer.from(await image.arrayBuffer()).subarray(0, 3).toString(), 'GIF', 'Offline animation is not a GIF');
  if (video) {
    const expectedVideo = await read(safePath(video));
    const request = range => new Request(new URL(video, h.scope), { headers: { Range: range } });
    const partial = await h.event('fetch', { request: request('bytes=0-31') });
    assert.equal(partial.status, 206, 'Offline video must support partial requests');
    assert.equal(partial.headers.get('Content-Range'), `bytes 0-31/${expectedVideo.length}`, 'Offline partial video has an incorrect content range');
    assert.equal(partial.headers.get('Content-Length'), '32');
    assert.deepEqual(Buffer.from(await partial.arrayBuffer()), expectedVideo.subarray(0, 32), 'Offline partial bytes differ from the full video');
    const suffix = await h.event('fetch', { request: request('bytes=-16') });
    assert.equal(suffix.status, 206, 'Offline video suffix request failed');
    assert.equal(suffix.headers.get('Content-Range'), `bytes ${expectedVideo.length - 16}-${expectedVideo.length - 1}/${expectedVideo.length}`);
    assert.deepEqual(Buffer.from(await suffix.arrayBuffer()), expectedVideo.subarray(-16), 'Offline suffix bytes differ from the full video');
    const invalid = await h.event('fetch', { request: request(`bytes=${expectedVideo.length}-`) });
    assert.equal(invalid.status, 416, 'Out-of-bounds video range must return 416');
    assert.equal(invalid.headers.get('Content-Range'), `bytes */${expectedVideo.length}`);
    const whole = await h.event('fetch', { request: new Request(new URL(video, h.scope)) });
    assert.equal(whole.status, 200, 'Partial requests must not replace the cached full video');
    assert.deepEqual(Buffer.from(await whole.arrayBuffer()), expectedVideo, 'Cached full video changed after partial requests');
  }
  const missing = await h.event('fetch', { request: new Request(h.scope + 'missing-image.gif') });
  assert.equal(missing.status, 503, 'Missing offline files must return an error');
  h.setOffline(false);
  h.setFailure(gif.replace(/^\.\//, ''));
  const retry = await h.message('DOWNLOAD_OFFLINE');
  assert(retry.some(m => m.type === 'OFFLINE_ERROR') && !retry.some(m => m.type === 'OFFLINE_READY'), 'Failed retry was marked ready');
  assert.equal((await h.message('CHECK_OFFLINE'))[0].type, 'OFFLINE_STATUS', 'Failed retry left the previous ready marker');
  const broken = await workerHarness(manifest, { fail: gif.replace(/^\.\//, '') });
  await broken.event('install');
  const failed = await broken.message('DOWNLOAD_OFFLINE');
  assert(failed.some(m => m.type === 'OFFLINE_ERROR') && !failed.some(m => m.type === 'OFFLINE_READY'), 'Failed download was marked ready');
  assert.equal((await broken.message('CHECK_OFFLINE'))[0].type, 'OFFLINE_STATUS', 'Failed download persisted a ready marker');
  const mismatch = await workerHarness(manifest, { wrongVersion: true });
  await mismatch.event('install');
  const mismatchMessages = await mismatch.message('DOWNLOAD_OFFLINE');
  assert(mismatchMessages.some(m => m.type === 'OFFLINE_ERROR') && !mismatchMessages.some(m => m.type === 'OFFLINE_READY'), 'Version mismatch was marked ready');
  console.log('Service worker: install, scope cleanup, complete and failed downloads, version mismatch, and offline fetches passed.');
}
try {
  const { generated, gif, video } = await checkStatic();
  await checkUI();
  await checkWorker(generated, gif, video);
} catch (error) {
  console.error(`Check failed: ${error.stack || error}`);
  process.exitCode = 1;
}
