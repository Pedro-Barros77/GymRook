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
  const channels = color => (color.match(/[\d.]+/g) || []).slice(0, 3).map(Number);
  const green = button => { const [red, green, blue] = channels(win().getComputedStyle(button).backgroundColor); return green > red && green > blue; };
  const red = button => [win().getComputedStyle(button).color, win().getComputedStyle(button).backgroundColor].some(color => { const [r, g, b] = channels(color); return r > g * 1.2 && r > b * 1.2; });
  const trashOutline = button => { const path = button.querySelector('svg path'); if (!path) return false; const style = win().getComputedStyle(path); return style.fill === 'none' && style.stroke !== 'none'; };
  try {
    await boot();
    let store = win().GYMROOK_STORE;
    check(win().GYMROOK_TRACKING.isReady(), 'Real IndexedDB initialized');
    check(doc().querySelector('#start-workout'), 'Start button rendered');
    check(doc().querySelector('#start-workout svg') && green(doc().querySelector('#start-workout')), 'Start button has green styling and a play SVG');
    check(doc().querySelectorAll('[data-series-exercise]').length === 0, 'Workout listing remains compact without series controls');
    const id = 'incline-dumbbell-press';
    doc().querySelector('#start-workout').click();
    await wait(() => store.getActiveSession() && doc().querySelector('#finish-workout'));
    check(doc().querySelector('#finish-workout svg') && red(doc().querySelector('#finish-workout')), 'Finish button has red styling and a stop SVG');
    const startedAt = store.getActiveSession().startedAt;
    await route('#exercise/' + id);
    const summary = location => doc().querySelector(`[data-exercise-progress="${id}"][data-progress-location="${location}"]`);
    check(/0\s*(?:\/|de)\s*3/.test(summary('detail')?.textContent || ''), 'Detail header starts with zero completed sets');
    check(!doc().querySelector('#finish-workout-top'), 'Top finish control is absent on non-final exercise');
    check(doc().querySelectorAll('[data-series-exercise]').length === 1, 'Series card appears only for the opened exercise');
    const how = [...doc().querySelectorAll('h2')].find(heading => heading.textContent === 'Como fazer.');
    check(Boolean(how.compareDocumentPosition(card(id)) & 4), 'Personal series follow Como fazer');
    const notes = doc().querySelector('#exercise-notes');
    check([...doc().querySelectorAll('main section')].at(-1) === notes && Boolean(card(id).compareDocumentPosition(notes) & 4) && Boolean(notes.compareDocumentPosition(doc().querySelector('.detail-nav-bottom')) & 4) && notes.querySelectorAll('textarea').length === 2, 'Both note fields follow series as the final content before bottom navigation');
    action(id, 'edit');
    type(card(id).querySelector('[data-field="weight"]'), '20,5');
    type(card(id).querySelector('[data-field="reps"]'), '12');
    action(id, 'done');
    await wait(() => store.getExercise(id).weights[0] === 20.5 && !card(id).querySelector('input'));
    check(store.getExercise(id).weights.length === 1, 'Decimal load and optional blank weights saved');
    const privateText = 'Banco 3 <script>window.noteInjected=true</script>\nControle & postura';
    const sessionText = 'Última série: esforço 8/10\nSem impulso hoje.';
    const progressionBeforeNotes = store.getState().progression.length;
    type(doc().querySelector('#exercise-private-note'), privateText);
    type(doc().querySelector('#exercise-session-note'), sessionText);
    await route('#exercise/high-cable-crossover');
    check(store.getExerciseNote(id) === privateText && store.getActiveSession().exercises[id].notes === sessionText, 'Fast exercise navigation flushes private and session notes');
    check(store.getState().progression.length === progressionBeforeNotes, 'Notes do not create load progression points');
    await route('#exercise/' + id);
    check(doc().querySelector('#exercise-private-note').value === privateText && !win().noteInjected, 'Private notes render escaped literal text');
    action(id, 'complete');
    await wait(() => store.getActiveSession().exercises[id].completed[0]);
    check(/1\s*(?:\/|de)\s*3/.test(summary('detail')?.textContent || '') && !summary('detail').classList.contains('is-complete'), 'Partial completion remains neutral in detail header');
    for (let index = 1; index < 3; index++) { card(id).querySelectorAll('[data-series-action="complete"]')[index].click(); await wait(() => store.getActiveSession().exercises[id].completed[index]); }
    check(summary('detail').classList.contains('is-complete'), 'Completed exercise turns header summary green');
    doc().querySelector('#rest-toggle').click();
    await wait(() => store.getActiveSession().restStartedAt);
    const restedAt = store.getActiveSession().restStartedAt;
    check(store.getActiveSession().startedAt === startedAt, 'Rest leaves total workout timer running');
    await new Promise(resolve => { frame.addEventListener('load', resolve, {once: true}); win().location.reload(); });
    await boot();
    store = win().GYMROOK_STORE;
    check(store.getActiveSession().startedAt === startedAt && store.getActiveSession().restStartedAt === restedAt, 'Session and rest restored after real page reload');
    check(store.getActiveSession().exercises[id].completed[0], 'Completed set persisted across reload');
    check(doc().querySelector('#exercise-private-note').value === privateText && doc().querySelector('#exercise-session-note').value === sessionText, 'Both note scopes persist after a real page reload');
    await route('#workout/A');
    check(doc().querySelector(`[data-exercise="${id}"]`).classList.contains('is-completed') && /3\s*(?:\/|de)\s*3/.test(summary('list')?.textContent || ''), 'Active workout list shows completed exercise count and green card');
    const groupColor = channels(win().getComputedStyle(doc().querySelector('.combined-group')).backgroundColor);
    check(groupColor[2] > groupColor[0] && groupColor[2] > groupColor[1], 'Conjugated group background is blue');
    doc().querySelector('[data-workout="B"]').click();
    check(win().location.hash === '#workout/B', 'Workout tab keeps URL aligned with visible workout');
    doc().querySelector('.session-return').click();
    await wait(() => win().location.hash === '#workout/A' && doc().querySelector('#finish-workout'));
    check(store.getActiveSession().workoutId === 'A', 'Sticky resume link returns from another workout tab');
    doc().querySelector('#rest-toggle').click();
    await wait(() => store.getActiveSession().restStartedAt === null);
    const lastId = win().GYMROOK_DATA.workouts[0].blocks.flatMap(block => block.exerciseIds).at(-1);
    await route('#exercise/' + lastId);
    check(doc().querySelector('#finish-workout-top'), 'Last exercise exposes a top finish control');
    doc().querySelector('#finish-workout-top').click();
    check(doc().querySelector('#finish-dialog').open && store.getActiveSession(), 'Top finish opens a native confirmation dialog');
    doc().dispatchEvent(new (win().KeyboardEvent)('keydown', {key: 'Escape', bubbles: true}));
    check(win().location.hash === '#exercise/' + lastId, 'Escape handler keeps the exercise route while finish dialog is open');
    doc().querySelector('#finish-cancel').click();
    check(!doc().querySelector('#finish-dialog').open && store.getActiveSession(), 'Canceling finish preserves the active session');
    doc().querySelector('#finish-workout-top').click();
    doc().querySelector('#finish-confirm').click();
    await wait(() => win().location.hash === '#history' && doc().querySelector('.history-session'));
    check(!store.getActiveSession() && doc().querySelector('.history-calendar-day.has-workout'), 'Finished session visible in calendar');
    check(doc().querySelector('.history-exercise-notes p')?.textContent === sessionText, 'Finalized workout history displays saved session notes');
    const exported = await store.exportBackup();
    const snapshot = JSON.parse(exported);
    check(snapshot.state.sessions[0].exercises[id].weights[0] === 20.5, 'Finished session keeps load snapshot');
    const longHistory = JSON.parse(exported);
    const longSession = longHistory.state.sessions[0];
    longSession.endedAt = new Date().toISOString();
    longSession.startedAt = new Date(new Date(longSession.endedAt).getTime() - 58 * 3600000).toISOString();
    await store.importBackup(JSON.stringify(longHistory));
    await route('#workout/A'); await route('#history');
    check(doc().querySelector('.history-session').textContent.includes('58h'), 'History displays a 58-hour session without wrapping duration');
    const localInput = date => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}T${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:00`;
    const correctedStart = new Date(); correctedStart.setHours(9, 0, 0, 0);
    const correctedEnd = new Date(correctedStart.getTime() + 3600000);
    const editTimes = () => doc().querySelector('[data-edit-session="' + longSession.id + '"]').click();
    const timeField = key => doc().querySelector('[data-session-times="' + longSession.id + '"] [data-session-time="' + key + '"]');
    editTimes();
    timeField('startedAt').value = localInput(correctedStart);
    timeField('endedAt').value = localInput(correctedEnd);
    doc().querySelector('[data-cancel-session-times="' + longSession.id + '"]').click();
    check(store.getState().sessions[0].startedAt === longSession.startedAt, 'Canceling history time correction preserves original timestamps');
    editTimes();
    timeField('startedAt').value = localInput(correctedStart);
    timeField('endedAt').value = localInput(correctedEnd);
    doc().querySelector('[data-save-session-times="' + longSession.id + '"]').click();
    await wait(() => store.getState().sessions[0].startedAt === correctedStart.toISOString() && !doc().querySelector('[data-session-times]'));
    check(doc().querySelector('.history-session').textContent.includes('1h 00min'), 'Corrected history duration and selected calendar day update');
    check(store.getState().sessions[0].exercises[id].notes === sessionText, 'Editing session timestamps preserves exercise notes');
    await store.importBackup(exported);
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

    // Destructive-flow tests use only this temporary QA profile. Restore the
    // fixture afterward so screenshots retain meaningful history and progression.
    const deletionBase = await store.exportBackup();
    const deletionState = JSON.parse(deletionBase);
    const firstSession = deletionState.state.sessions[0];
    deletionState.state.sessions.push({...JSON.parse(JSON.stringify(firstSession)), id: firstSession.id + '-second'});
    const middleDate = new Date(); middleDate.setDate(middleDate.getDate() - 7);
    const localKey = value => `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`;
    const middleDay = localKey(middleDate);
    deletionState.state.progression.push({exerciseId: id, date: middleDay, editedAt: middleDate.toISOString(), weights: [18], reps: [10, 10, 10]});
    await store.importBackup(JSON.stringify(deletionState));
    await route('#history');
    const confirmed = win().confirm;
    win().confirm = () => false;
    const deleteSession = () => doc().querySelector('[data-delete-session]');
    check(deleteSession()?.querySelector('svg') && red(deleteSession()) && trashOutline(deleteSession()), 'History delete action uses red styling and an outlined trash SVG');
    deleteSession().click(); await fetch('/__tick');
    check(store.getState().sessions.length === 2, 'Canceling history deletion preserves sessions');
    win().confirm = () => true;
    deleteSession().click();
    await wait(() => store.getState().sessions.length === 1 && doc().querySelectorAll('.history-session').length === 1);
    check(doc().querySelector('[data-history-day="' + localKey(new Date(firstSession.startedAt)) + '"]').classList.contains('has-workout'), 'One remaining session keeps the calendar marker');
    deleteSession().click();
    await wait(() => store.getState().sessions.length === 0 && doc().querySelectorAll('.history-session').length === 0);
    check(!doc().querySelector('.history-calendar-day.has-workout'), 'Deleting final session removes the calendar marker');
    await route('#progression/' + id);
    const deletePoint = date => doc().querySelector('[data-delete-progression="' + date + '"]');
    check(deletePoint(middleDay)?.querySelector('svg') && red(deletePoint(middleDay)) && trashOutline(deletePoint(middleDay)), 'Progression delete action uses red styling and an outlined trash SVG');
    deletePoint(middleDay).click();
    await wait(() => doc().querySelectorAll('.history-chart-point').length === 2);
    check(store.getExercise(id).weights[0] === 20.5, 'Deleting middle progression point preserves current loads');
    const remaining = store.getState().progression.filter(point => point.exerciseId === id).sort((a, b) => a.date.localeCompare(b.date));
    win().confirm = () => false;
    deletePoint(remaining[1].date).click(); await fetch('/__tick');
    check(store.getState().progression.filter(point => point.exerciseId === id).length === 2, 'Canceling progression deletion preserves points');
    await route('#exercise/' + id);
    action(id, 'edit');
    await route('#progression/' + id);
    win().confirm = () => true;
    deletePoint(remaining[1].date).click();
    await wait(() => doc().querySelectorAll('.history-chart-point').length === 1);
    check(store.getExercise(id).weights[0] === 15, 'Deleting latest progression point restores previous settings');
    await route('#exercise/' + id);
    const restoredInput = card(id).querySelector('[data-field="weight"]');
    check(restoredInput ? Number(restoredInput.value.replace(',', '.')) === 15 : card(id).textContent.includes('15 kg'), 'Returning to detail shows restored load instead of deleted editor draft');
    await route('#progression/' + id);
    deletePoint(remaining[0].date).click();
    await wait(() => !doc().querySelector('.history-chart-point'));
    check(store.getExercise(id).weights.length === 0 && store.getExercise(id).reps.join(',') === '10,10,10', 'Deleting all progression restores defaults');
    win().confirm = confirmed;
    await store.importBackup(deletionBase);
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

// These previews modify only the disposable QA profile created below, giving
// visual review access to transient states that disappear after the smoke test.
async function previewBrowser(view) {
  const frame = document.querySelector('iframe');
  const wait = async predicate => { for (let index = 0; index < 400; index++) { if (predicate()) return; await fetch('/__tick'); } throw new Error('Preview did not become ready'); };
  await wait(() => frame.contentWindow.GYMROOK_TRACKING?.isReady());
  const win = frame.contentWindow, doc = frame.contentDocument, store = win.GYMROOK_STORE;
  await fetch('/__tick');
  const id = 'incline-dumbbell-press';
  if (['active-workout', 'active-detail', 'active-notes', 'finish-confirmation'].includes(view)) {
    const workout = win.GYMROOK_DATA.workouts.find(item => item.id === 'A');
    const ids = workout.blocks.flatMap(block => block.exerciseIds);
    if (!store.getActiveSession()) await store.startSession('A', ids);
    for (let index = 0; index < store.getActiveSession().exercises[id].reps.length; index++) if (!store.getActiveSession().exercises[id].completed[index]) await store.toggleSet(id, index);
    await store.updateExerciseNote(id, 'Banco no pino 3. Apoiar os pés e controlar a descida.');
    await store.updateSessionExerciseNote(id, 'Última série exigiu mais esforço; mantive a postura.', store.getActiveSession().id);
    if (view === 'finish-confirmation') {
      await wait(() => doc.querySelector('#finish-workout-top'));
      doc.querySelector('#finish-workout-top').click();
    }
  }
  if (view === 'history-edit') {
    if (store.getActiveSession()) await store.finishSession();
    const session = store.getState().sessions.filter(item => item.endedAt).sort((a, b) => b.startedAt.localeCompare(a.startedAt))[0];
    const end = new Date(), start = new Date(end.getTime() - 58 * 3600000);
    await store.updateSessionTimes(session.id, {startedAt: start.toISOString(), endedAt: end.toISOString()});
    win.GYMROOK_HISTORY.render(doc.getElementById('main'), '#history');
    const date = `${start.getFullYear()}-${String(start.getMonth() + 1).padStart(2, '0')}-${String(start.getDate()).padStart(2, '0')}`;
    for (let index = 0; index < 3 && !doc.querySelector(`[data-history-day="${date}"]`); index++) doc.querySelector('#history-month-prev').click();
    doc.querySelector(`[data-history-day="${date}"]`).click();
    doc.querySelector(`[data-edit-session="${session.id}"]`).click();
  }
  const reveal = () => {
    doc.documentElement.style.scrollBehavior = 'auto';
    if (view === 'detail' || view === 'active-notes') win.scrollTo({top: 100000, behavior: 'instant'});
    else if (view === 'history-edit') doc.querySelector('.history-session').scrollIntoView({block: 'start', behavior: 'instant'});
    else win.scrollTo({top: 0, behavior: 'instant'});
  };
  reveal();
  setInterval(reveal, 50);
}

const page = (route, script) => `<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>html,body{margin:0;width:100%;height:100%;background:#dedfd7}iframe{margin:auto;width:360px;max-width:100%;height:100%;border:0;display:block}</style><iframe src="/${route}"></iframe><script>${script.replace(/<\/script/gi, '<\\/script')}</script>`;
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
      const routes = {workout:'#workout/A',detail:'#exercise/incline-dumbbell-press',history:'#history',progression:'#progression/incline-dumbbell-press',backup:'#backup','active-workout':'#workout/A','active-detail':'#exercise/incline-dumbbell-press','active-notes':'#exercise/incline-dumbbell-press','finish-confirmation':'#exercise/forearm-plank','history-edit':'#history'};
      const view = url.searchParams.get('view');
      const html = page(routes[view] || routes.progression, `(${previewBrowser.toString()})(${JSON.stringify(view)});`);
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
  for (const view of ['workout','detail','history','progression','backup','active-workout','active-detail','active-notes','finish-confirmation','history-edit']) {
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
