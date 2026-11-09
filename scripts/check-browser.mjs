import assert from 'node:assert/strict';
import http from 'node:http';
import path from 'node:path';
import { readFile, mkdir, writeFile, access } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';

// Optional real-browser smoke test. Uses a separate profile and a private HTTP
// server; never reads or changes the user's browser data. No browser installation.
const root = fileURLToPath(new URL('../dist/', import.meta.url));
const output = fileURLToPath(new URL(`../output/browser-qa/${Date.now()}/`, import.meta.url));
const browser = process.env.GYMROOK_BROWSER || 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
await access(browser);
await mkdir(output, {recursive: true});

async function browserTest() {
  const results = [];
  const frame = document.querySelector('iframe');
  const check = (condition, message) => { if (!condition) throw new Error(message); results.push(message); };
  const wait = async condition => {
    // A real network heartbeat lets filesystem/IDB I/O progress even when Edge
    // advances its headless virtual clock faster than wall time.
    for (let i = 0; i < 400; i++) { if (condition()) return; await fetch('/__tick'); }
    throw new Error('Timeout waiting for UI');
  };
  const boot = async () => { await wait(() => frame.contentWindow.GYMROOK_TRACKING); await frame.contentWindow.GYMROOK_TRACKING.ready; };
  const doc = () => frame.contentDocument;
  const win = () => frame.contentWindow;
  const card = id => doc().querySelector(`[data-series-exercise="${id}"]`);
  const action = (id, name) => card(id).querySelector(`[data-series-action="${name}"]`).click();
  const route = async hash => { win().location.hash = hash; await wait(() => doc().querySelector('h1')); await new Promise(resolve => setTimeout(resolve, 80)); };
  const type = (input, value) => { input.value = value; input.dispatchEvent(new (win().Event)('input', {bubbles: true})); };
  try {
    await boot();
    let store = win().GYMROOK_STORE;
    check(win().GYMROOK_TRACKING.isReady(), 'Real IndexedDB initialized');
    check(doc().querySelector('#start-workout'), 'Start button rendered');
    check(doc().querySelectorAll('[data-series-exercise]').length === 0, 'Workout listing remains compact without series controls');
    const id = 'incline-dumbbell-press';
    doc().querySelector('#start-workout').click();
    await wait(() => store.getActiveSession() && doc().querySelector('#finish-workout'));
    const startedAt = store.getActiveSession().startedAt;
    await route('#exercise/' + id);
    check(doc().querySelectorAll('[data-series-exercise]').length === 1, 'Series card appears only for the opened exercise');
    const how = [...doc().querySelectorAll('h2')].find(heading => heading.textContent === 'Como fazer.');
    check(Boolean(how.compareDocumentPosition(card(id)) & 4), 'Personal series follow Como fazer');
    check([...doc().querySelectorAll('main section')].at(-1) === card(id) && Boolean(card(id).compareDocumentPosition(doc().querySelector('.detail-nav-bottom')) & 4), 'Series are the final content before bottom navigation');
    action(id, 'edit');
    type(card(id).querySelector('[data-field="weight"]'), '20,5');
    type(card(id).querySelector('[data-field="reps"]'), '12');
    action(id, 'done');
    await wait(() => store.getExercise(id).weights[0] === 20.5 && !card(id).querySelector('input'));
    check(store.getExercise(id).weights.length === 1, 'Decimal load and optional blank weights saved');
    action(id, 'complete');
    await wait(() => store.getActiveSession().exercises[id].completed[0]);
    doc().querySelector('#rest-toggle').click();
    await wait(() => store.getActiveSession().restStartedAt);
    const restedAt = store.getActiveSession().restStartedAt;
    check(store.getActiveSession().startedAt === startedAt, 'Rest leaves total workout timer running');
    await new Promise(resolve => { frame.addEventListener('load', resolve, {once: true}); win().location.reload(); });
    await boot();
    store = win().GYMROOK_STORE;
    check(store.getActiveSession().startedAt === startedAt && store.getActiveSession().restStartedAt === restedAt, 'Session and rest restored after real page reload');
    check(store.getActiveSession().exercises[id].completed[0], 'Completed set persisted across reload');
    await route('#workout/A');
    doc().querySelector('[data-workout="B"]').click();
    check(win().location.hash === '#workout/B', 'Workout tab keeps URL aligned with visible workout');
    doc().querySelector('.session-return').click();
    await wait(() => win().location.hash === '#workout/A' && doc().querySelector('#finish-workout'));
    check(store.getActiveSession().workoutId === 'A', 'Sticky resume link returns from another workout tab');
    doc().querySelector('#rest-toggle').click();
    await wait(() => store.getActiveSession().restStartedAt === null);
    doc().querySelector('#finish-workout').click();
    await wait(() => win().location.hash === '#history' && doc().querySelector('.history-session'));
    check(!store.getActiveSession() && doc().querySelector('.history-calendar-day.has-workout'), 'Finished session visible in calendar');
    const exported = await store.exportBackup();
    const snapshot = JSON.parse(exported);
    check(snapshot.state.sessions[0].exercises[id].weights[0] === 20.5, 'Finished session keeps load snapshot');
    check(typeof store.getDailyBackup === 'undefined' && typeof store.connectBackupFile === 'undefined', 'Automatic and linked backup features removed');
    if (win().navigator.storage?.getDirectory) {
      const dir = await win().navigator.storage.getDirectory();
      let hasSnapshot = false;
      try { await dir.getFileHandle('gymrook-backup.json'); hasSnapshot = true; } catch (error) { if (error.name !== 'NotFoundError') throw error; }
      check(!hasSnapshot, 'No automatic snapshot file created during workout');
    }
    await route('#backup');
    check(doc().querySelector('#backup-export') && doc().querySelector('#backup-import') && !doc().querySelector('#backup-daily') && !doc().querySelector('#backup-connect'), 'Backup screen offers manual export and import only');
    await store.updateExercise(id, {weights: [30], reps: [8, 8, 8]});
    check(store.getState().sessions[0].exercises[id].reps[0] === 12, 'Editing after finish preserves session history');
    await store.importBackup(exported);
    check(store.getExercise(id).weights[0] === 20.5, 'Backup restoration replaces edited configuration');
    const current = JSON.parse(await store.exportBackup());
    const date = new Date(); date.setDate(date.getDate() - 14);
    const localDay = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    current.state.progression.unshift({exerciseId: id, date: localDay, editedAt: date.toISOString(), weights: [15], reps: [10, 10, 10]});
    await store.importBackup(JSON.stringify(current));
    await route('#progression/' + id);
    await wait(() => doc().querySelectorAll('.history-chart-point').length === 2);
    check(doc().querySelectorAll('.progression-day').length === 2, 'Two dated edits render two real SVG points and daily details');
    check(doc().documentElement.scrollWidth <= doc().documentElement.clientWidth, 'Mobile viewport has no horizontal overflow');
    await route('#workout/A');
    doc().querySelector('#start-workout').click();
    await wait(() => store.getActiveSession());
    const timed = JSON.parse(await store.exportBackup());
    const session = timed.state.sessions.find(item => !item.endedAt);
    session.startedAt = new Date(Date.now() - 7200000).toISOString();
    session.restStartedAt = new Date(Date.now() - 3605000).toISOString();
    await store.importBackup(JSON.stringify(timed));
    await wait(() => doc().querySelector('#workout-clock')?.textContent.startsWith('02:'));
    check(doc().documentElement.scrollWidth <= doc().documentElement.clientWidth, 'Long workout and rest clocks fit mobile viewport');
    await store.finishSession();
    await route('#progression/' + id);
    await fetch('/__report', {method: 'POST', body: JSON.stringify({ok: true, results, userAgent: navigator.userAgent, viewport: {width: doc().documentElement.clientWidth, height: doc().documentElement.clientHeight}})});
  } catch (error) {
    await fetch('/__report', {method: 'POST', body: JSON.stringify({ok: false, results, error: error.stack || String(error), status: doc().querySelector('#tracking-status')?.textContent, state: win().GYMROOK_STORE?.getState(), sample: doc().querySelector('[data-series-exercise]')?.outerHTML})});
  }
}

const page = (route, script) => `<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>html,body{margin:0;width:100%;height:100%;background:#dedfd7}iframe{margin:auto;width:360px;max-width:100%;height:100%;border:0;display:block}</style><iframe src="/${route}"></iframe><script>${script}</script>`;
const qa = page('', `(${browserTest.toString()})();`);
let reportResolve;
const reported = new Promise(resolve => { reportResolve = resolve; });
const types = {'.js':'text/javascript', '.css':'text/css', '.html':'text/html', '.json':'application/json', '.webmanifest':'application/manifest+json', '.png':'image/png', '.webp':'image/webp', '.gif':'image/gif', '.mp4':'video/mp4'};
const server = http.createServer(async (request, response) => {
  try {
    const url = new URL(request.url, 'http://localhost');
    if (url.pathname === '/__tick') { await new Promise(resolve => setTimeout(resolve, 20)); response.end('tick'); return; }
    if (url.pathname === '/__report') {
      let body = ''; for await (const chunk of request) body += chunk;
      response.end('ok'); reportResolve(JSON.parse(body)); return;
    }
    if (url.pathname === '/__qa') { response.writeHead(200, {'Content-Type':'text/html; charset=utf-8'}).end(qa); return; }
    if (url.pathname === '/__preview') {
      const routes = {workout:'#workout/A',detail:'#exercise/incline-dumbbell-press',history:'#history',progression:'#progression/incline-dumbbell-press',backup:'#backup'};
      const view = url.searchParams.get('view');
      const html = page(routes[view] || routes.progression, `(async()=>{const frame=document.querySelector('iframe');while(!frame.contentWindow.GYMROOK_TRACKING?.isReady()){await fetch('/__tick');}${view === 'detail' ? "await fetch('/__tick');const reveal=()=>{frame.contentDocument.documentElement.style.scrollBehavior='auto';frame.contentWindow.scrollTo({top:100000,behavior:'instant'});};reveal();setInterval(reveal,50);" : ''}})();`);
      response.writeHead(200, {'Content-Type':'text/html; charset=utf-8'}).end(html); return;
    }
    const file = path.resolve(root, '.' + (url.pathname === '/' ? '/index.html' : decodeURIComponent(url.pathname)));
    if (!file.startsWith(root)) { response.writeHead(403).end(); return; }
    const body = await readFile(file);
    response.writeHead(200, {'Content-Type': `${types[path.extname(file)] || 'application/octet-stream'}; charset=utf-8`, 'Cache-Control':'no-store'}).end(body);
  } catch { response.writeHead(404).end(); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const port = server.address().port;
const screenshot = path.join(output, 'mobile-progression.png');
const profile = path.join(output, 'profile');
const child = spawn(browser, ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check', `--user-data-dir=${profile}`, '--window-size=390,844', '--hide-scrollbars', '--remote-debugging-port=0', `http://127.0.0.1:${port}/__qa`], {stdio: ['ignore', 'ignore', 'pipe'], windowsHide: true});
let logs = ''; child.stderr.on('data', data => { logs = (logs + data).slice(-8000); });
const timeout = setTimeout(() => reportResolve({ok:false, error: 'Browser smoke test timed out', logs}), 45000);
try {
  const result = await reported;
  await writeFile(path.join(output, 'report.json'), JSON.stringify(result, null, 2));
  assert(result.ok, JSON.stringify(result, null, 2));
  const stopped = new Promise(resolve => child.once('exit', resolve));
  child.kill();
  await Promise.race([stopped, new Promise(resolve => setTimeout(resolve, 5000))]);
  for (const view of ['workout','detail','history','progression','backup']) {
    const target = path.join(output, `mobile-${view}.png`);
    const capture = spawn(browser, ['--headless=new', '--disable-gpu', '--no-first-run', `--user-data-dir=${profile}`, '--window-size=520,1000', '--hide-scrollbars', '--virtual-time-budget=2000', `--screenshot=${target}`, `http://127.0.0.1:${port}/__preview?view=${view}`], {stdio:'ignore', windowsHide:true});
    await Promise.race([new Promise(resolve => capture.once('exit', resolve)), new Promise(resolve => setTimeout(resolve, 10000))]);
    capture.kill();
    await access(target);
  }
  console.log(JSON.stringify({...result, screenshot}, null, 2));
} finally {
  clearTimeout(timeout);
  child.kill();
  server.closeAllConnections();
  server.close();
}
