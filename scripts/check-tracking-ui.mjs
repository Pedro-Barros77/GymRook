import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { harness } from './check-ui.mjs';

// This exercises rendering and bound controls with a storage fixture. Durable
// IndexedDB and import validation have separate model tests.
const root = new URL('../dist/', import.meta.url);
const read = name => readFile(new URL(name, root), 'utf8');
const clone = value => structuredClone(value);
const settle = async () => { for (let i = 0; i < 4; i++) await new Promise(resolve => setImmediate(resolve)); };
const day = value => { const date = new Date(value); return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`; };

function fixture(now) {
  let state = { schemaVersion: 1, updatedAt: new Date(now()).toISOString(), settings: {}, exerciseNotes: {}, sessions: [], progression: [] };
  const listeners = new Set();
  let nextError = null;
  let clock = now;
  const active = () => state.sessions.find(session => !session.endedAt) || null;
  const setting = id => clone(state.settings[id] || { weights: [], reps: [10, 10, 10] });
  const emit = () => { state.updatedAt = new Date(clock()).toISOString(); for (const listener of listeners) listener(); };
  const mutate = fn => {
    if (nextError) { const error = nextError; nextError = null; return Promise.reject(error); }
    const result = fn(); emit(); return Promise.resolve(clone(result));
  };
  const store = {
    ready: Promise.resolve(), getState: () => clone(state), getActiveSession: () => clone(active()), getExercise: setting,
    subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener); },
    startSession(workoutId, exerciseIds) { return mutate(() => {
      if (active()) throw new Error('Já existe treino em andamento.');
      const session = { id: `session-${state.sessions.length + 1}`, workoutId, startedAt: new Date(clock()).toISOString(), endedAt: null, restStartedAt: null,
        exercises: Object.fromEntries(exerciseIds.map(id => { const config = setting(id); return [id, { weights: config.weights, reps: config.reps, completed: config.reps.map(() => false), notes: '' }]; })) };
      state.sessions.push(session); return session;
    }); },
    toggleRest() { return mutate(() => { if (!active()) throw new Error('Nenhum treino ativo.'); active().restStartedAt = active().restStartedAt ? null : new Date(clock()).toISOString(); return active(); }); },
    finishSession() { return mutate(() => { if (!active()) throw new Error('Nenhum treino ativo.'); const session = active(); session.endedAt = new Date(clock()).toISOString(); session.restStartedAt = null; return session; }); },
    updateExercise(id, config) { return mutate(() => {
      const weights = clone(config.weights), reps = clone(config.reps), updatedAt = new Date(clock()).toISOString();
      while (weights.length && weights.at(-1) == null) weights.pop();
      state.settings[id] = { weights, reps, updatedAt };
      if (active()?.exercises[id]) {
        const entry = active().exercises[id];
        entry.completed = reps.map((value, index) => entry.reps[index] === value && (entry.weights[index] ?? null) === (weights[index] ?? null) && Boolean(entry.completed[index]));
        entry.weights = weights; entry.reps = reps;
      }
      const point = { exerciseId: id, date: day(clock()), editedAt: updatedAt, weights, reps };
      const index = state.progression.findIndex(item => item.exerciseId === id && item.date === point.date);
      if (index < 0) state.progression.push(point); else state.progression[index] = point;
      return state.settings[id];
    }); },
    toggleSet(id, index) { return mutate(() => { if (!active()?.exercises[id]) throw new Error('Inicie o treino antes de marcar séries.'); const entry = active().exercises[id]; entry.completed[index] = !entry.completed[index]; return entry; }); },
    getExerciseNote: id => state.exerciseNotes?.[id] || '',
    updateExerciseNote(id, text) { return mutate(() => {
      if (typeof text !== 'string' || text.length > 4000) throw new Error('Use até 4000 caracteres na anotação.');
      state.exerciseNotes ||= {};
      if (text) state.exerciseNotes[id] = text; else delete state.exerciseNotes[id];
      return text;
    }); },
    updateSessionExerciseNote(id, text, expectedSessionId) { return mutate(() => {
      if (!active()?.exercises[id] || expectedSessionId && active().id !== expectedSessionId) throw new Error('O treino desta anotação não está mais em andamento.');
      if (typeof text !== 'string' || text.length > 4000) throw new Error('Use até 4000 caracteres na anotação.');
      active().exercises[id].notes = text; return text;
    }); },
    updateSessionTimes(id, value) { return mutate(() => {
      const session = state.sessions.find(item => item.id === id && item.endedAt);
      if (!session) throw new Error('Treino finalizado não encontrado.');
      const start = new Date(value.startedAt).getTime(), end = new Date(value.endedAt).getTime();
      if (!Number.isFinite(start) || !Number.isFinite(end) || end < start) throw new Error('O fim do treino deve ser posterior ao início.');
      session.startedAt = new Date(start).toISOString(); session.endedAt = new Date(end).toISOString();
      return session;
    }); },
    deleteSession(id) { return mutate(() => {
      const index = state.sessions.findIndex(session => session.id === id);
      if (index < 0 || !state.sessions[index].endedAt) throw new Error('Treino não encontrado ou em andamento.');
      return state.sessions.splice(index, 1)[0];
    }); },
    deleteProgression(id, date) { return mutate(() => {
      const records = state.progression.filter(point => point.exerciseId === id).sort((a, b) => b.date.localeCompare(a.date) || b.editedAt.localeCompare(a.editedAt));
      const target = records.find(point => point.date === date);
      if (!target) throw new Error('Registro de progressão não encontrado.');
      state.progression = state.progression.filter(point => point !== target);
      if (records[0] === target) {
        const latest = records[1];
        if (latest) state.settings[id] = { weights: clone(latest.weights), reps: clone(latest.reps), updatedAt: latest.editedAt };
        else delete state.settings[id];
        const entry = active()?.exercises[id];
        if (entry) {
          const next = setting(id);
          entry.completed = next.reps.map((reps, index) => entry.reps[index] === reps && (entry.weights[index] ?? null) === (next.weights[index] ?? null) && Boolean(entry.completed[index]));
          entry.weights = next.weights; entry.reps = next.reps;
        }
      }
      return target;
    }); },
    exportBackup: async () => JSON.stringify({ app: 'GymRook', formatVersion: 1, exportedAt: new Date(clock()).toISOString(), state }),
    importBackup: async text => { state = clone(JSON.parse(text).state); emit(); },
    setClock: fn => { clock = fn; }, failNext: error => { nextError = error; }, replace: value => { state = clone(value); emit(); }
  };
  return store;
}

function card(ui, id) {
  const result = ui.main.querySelectorAll('[data-series-exercise]').find(element => element.dataset.seriesExercise === id);
  assert(result, `${id}: series card missing`);
  return result;
}
function action(element, name) {
  const result = element.querySelector(`[data-series-action="${name}"]`);
  assert(result, `Missing series action ${name}`);
  return result;
}
function input(element, field, index) {
  const result = element.querySelectorAll(`[data-field="${field}"]`).find(node => node.dataset.seriesIndex === String(index));
  assert(result, `Missing ${field} input for series ${index}`);
  return result;
}
async function openSeries(ui, id) {
  ui.location.hash = '#exercise/' + id;
  await settle();
  assert.equal(ui.main.querySelectorAll('[data-series-exercise]').length, 1, 'Exercise detail must contain exactly its own series card');
  const series = card(ui, id);
  const nodes = [];
  const walk = node => { for (const child of node.children || []) if (typeof child !== 'string') { nodes.push(child); walk(child); } };
  walk(ui.main);
  const how = ui.main.querySelectorAll('h2').find(node => node.textContent === 'Como fazer.');
  const bottom = ui.main.querySelector('.detail-nav-bottom');
  const notes = ui.main.querySelector('#exercise-notes');
  assert(how && nodes.indexOf(how) < nodes.indexOf(series), 'Personal series must follow Como fazer');
  assert(notes && nodes.indexOf(series) < nodes.indexOf(notes), 'Both exercise note fields must follow personal series');
  assert.equal(ui.main.querySelectorAll('section').at(-1), notes, 'Exercise notes must be the last content section');
  assert(notes.querySelector('#exercise-private-note') && notes.querySelector('#exercise-session-note'), 'Final notes section must contain both note fields');
  assert(nodes.indexOf(notes) < nodes.indexOf(bottom), 'Exercise notes must precede the bottom previous/next buttons');
  return series;
}

async function checkHistoryScreens(html) {
  const scripts = await Promise.all(['data.js', 'history.js'].map(async name => [name, await read(name)]));
  const now = new Date(2026, 10, 9, 10).getTime();
  const store = fixture(() => now);
  const ui = harness(html, scripts, '', { now, window: { GYMROOK_STORE: store } });
  const id = ui.data.workouts[0].blocks[0].exerciseIds[0];
  const started = new Date(2026, 10, 8, 23, 50).toISOString();
  const ended = new Date(2026, 10, 9, 0, 20).toISOString();
  store.replace({ schemaVersion: 1, updatedAt: ended, settings: {}, sessions: [
    { id: 'late', workoutId: 'A', startedAt: started, endedAt: ended, exercises: { [id]: { weights: [12, 14, 14], reps: [10, 10, 8], completed: [true, true, true] } } },
    { id: 'early', workoutId: 'B', startedAt: new Date(2026, 10, 8, 8).toISOString(), endedAt: new Date(2026, 10, 8, 8, 40).toISOString(), exercises: { [id]: { weights: [], reps: [10, 10, 10], completed: [true, false, false] } } },
    { id: 'ongoing', workoutId: 'C', startedAt: new Date(2026, 10, 9, 9).toISOString(), endedAt: null, exercises: {} }
  ], progression: [
    { exerciseId: id, date: '2026-11-08', editedAt: new Date(2026, 10, 8, 9).toISOString(), weights: [8, 10], reps: [10, 10] },
    { exerciseId: id, date: '2026-11-08', editedAt: new Date(2026, 10, 8, 17).toISOString(), weights: [10, 12], reps: [10, 12] },
    { exerciseId: id, date: '2026-11-22', editedAt: new Date(2026, 10, 22, 9).toISOString(), weights: [12, 14, 14], reps: [12, 10, 10] }
  ] });
  ui.window.GYMROOK_HISTORY.render(ui.main, '#history');
  assert.equal(ui.main.querySelectorAll('.history-session').length, 2, 'All sessions on selected day must be shown');
  const trained = ui.main.querySelector('[data-history-day="2026-11-08"]');
  assert(trained.classList.contains('has-workout'), 'Completed workout day is not marked');
  assert(trained.getAttribute('aria-label').includes('2 treinos'), 'Same-day workouts must share one calendar day');
  assert(!ui.main.querySelector('[data-history-day="2026-11-09"]').classList.contains('has-workout'), 'Ongoing workout must not count as finalized');
  assert(ui.main.querySelectorAll('.history-session')[0].textContent.includes('30min'), 'Session duration across midnight is wrong');
  assert(ui.main.querySelectorAll('.history-session')[0].textContent.includes('1 de 1'), 'Completed exercise count is wrong');
  assert(ui.main.querySelectorAll('.history-session')[1].textContent.includes('0 de 1'), 'Partial exercise must not count as completed');
  ui.main.querySelector('[data-history-day="2026-11-09"]').click();
  assert.equal(ui.main.querySelectorAll('.history-session').length, 0);
  assert(ui.main.textContent.includes('em andamento'), 'Selected active workout day lacks ongoing notice');
  ui.main.querySelector('#history-month-prev').click();
  assert(ui.main.querySelector('#history-month').textContent.includes('outubro'), 'Previous calendar month navigation failed');
  ui.main.querySelector('#history-month-next').click();
  assert(ui.main.querySelector('#history-month').textContent.includes('novembro'), 'Next calendar month navigation failed');
  ui.main.querySelector('#history-today').click();
  assert.equal(ui.main.querySelector('[data-history-day="2026-11-09"]').getAttribute('aria-pressed'), 'true');

  ui.window.GYMROOK_HISTORY.render(ui.main, '#progression/' + id);
  assert.equal(ui.main.querySelector('#progression-exercise').querySelectorAll('option').length, 31, 'Progression must allow every catalog exercise');
  assert.equal(ui.main.querySelectorAll('.history-chart-point').length, 2, 'Repeated edits on the same day must produce one chart point');
  assert.equal(ui.main.querySelectorAll('.progression-day').length, 2, 'Repeated edits on the same day must produce one detail entry');
  const points = ui.main.querySelectorAll('.history-chart-point');
  assert(points[0].textContent.includes('12 kg') && points[1].textContent.includes('14 kg'), 'Load chart must use maximum load from last edit of each day');
  assert(!ui.main.textContent.includes('NaN') && !ui.main.textContent.includes('undefined'), 'Chart contains invalid data');
  let metric = ui.main.querySelector('#progression-metric');
  metric.value = 'reps'; metric.dispatch('change');
  assert(ui.main.querySelectorAll('.history-chart-point')[0].textContent.includes('22 rep.'), 'Repetition chart must sum configured sets');
  metric = ui.main.querySelector('#progression-metric'); metric.value = 'sets'; metric.dispatch('change');
  assert(ui.main.querySelectorAll('.history-chart-point')[0].textContent.includes('2 séries'), 'Set chart is wrong');
  const exerciseSelect = ui.main.querySelector('#progression-exercise');
  exerciseSelect.value = 'forearm-plank'; exerciseSelect.dispatch('change');
  assert.equal(ui.main.querySelectorAll('.history-chart-point').length, 0, 'No-history exercise must not invent progression points');
  assert(ui.main.textContent.includes('Ainda não há ajustes'), 'No-history exercise lacks useful empty state');
}

async function checkSessionTimeEditing(html) {
  const scripts = await Promise.all(['data.js', 'history.js'].map(async name => [name, await read(name)]));
  const now = new Date(2026, 10, 18, 10).getTime();
  const store = fixture(() => now);
  const ui = harness(html, scripts, '', {now, window: {GYMROOK_STORE: store, confirm: () => true}});
  const id = ui.data.workouts[0].blocks[0].exerciseIds[0];
  const startedAt = new Date(2026, 10, 15, 7).toISOString(), endedAt = new Date(2026, 10, 17, 17).toISOString();
  const note = 'Banco no ajuste 3\n<script>window.bad = true</script> & "controle"';
  store.replace({schemaVersion: 1, updatedAt: endedAt, settings: {}, exerciseNotes: {}, progression: [], sessions: [{id: 'long', workoutId: 'A', startedAt, endedAt, restStartedAt: null,
    exercises: {[id]: {weights: [20], reps: [10], completed: [true], notes: note}}}]});
  ui.window.GYMROOK_HISTORY.render(ui.main, '#history');
  assert(ui.main.querySelector('.history-session').textContent.includes('58h'), 'History must preserve durations exceeding one day');
  assert.equal(ui.main.querySelector('.history-exercise-notes p').textContent, note, 'Historical exercise note must display its literal saved text');
  assert.equal(ui.main.querySelectorAll('script').length, 0, 'Historical note HTML was interpreted as markup');
  const edit = () => ui.main.querySelector('[data-edit-session="long"]');
  const form = () => ui.main.querySelector('[data-session-times="long"]');
  const field = name => form().querySelector(`[data-session-time="${name}"]`);
  edit().click();
  field('startedAt').value = '2026-11-18T10:00:00';
  field('endedAt').value = '2026-11-18T11:00:00';
  ui.main.querySelector('[data-cancel-session-times="long"]').click();
  assert.equal(store.getState().sessions[0].startedAt, startedAt, 'Canceling time edits changed session data');
  assert(!form(), 'Canceling time edits did not close the form');

  edit().click();
  field('startedAt').value = '2026-11-18T20:00:00';
  field('endedAt').value = '2026-11-18T19:00:00';
  form().dispatch('submit'); await settle();
  assert.equal(store.getState().sessions[0].endedAt, endedAt, 'Invalid time interval changed the session');
  assert(form().querySelector('.history-time-error').textContent, 'Invalid time interval needs a visible error');
  field('endedAt').value = '2026-11-19T00:30:00';
  store.failNext(new Error('Sem espaço para corrigir o horário'));
  form().dispatch('submit'); await settle();
  assert.equal(store.getState().sessions[0].startedAt, startedAt, 'Failed time edit changed the session');
  assert(form().querySelector('.history-time-error').textContent.includes('Sem espaço'), 'Time-save failure was not explained');
  assert(!ui.main.querySelector('[data-save-session-times="long"]').disabled, 'Failed time edit left the form stuck');
  form().dispatch('submit'); await settle();
  const saved = store.getState().sessions[0];
  assert.equal(saved.startedAt, new Date(2026, 10, 18, 20).toISOString());
  assert.equal(saved.endedAt, new Date(2026, 10, 19, 0, 30).toISOString());
  assert.equal(saved.exercises[id].notes, note, 'Editing timestamps changed exercise notes');
  assert.deepEqual(saved.exercises[id].completed, [true], 'Editing timestamps changed completed sets');
  assert(!ui.main.querySelector('[data-history-day="2026-11-15"]').classList.contains('has-workout'), 'Time correction left the old calendar day marked');
  assert(ui.main.querySelector('[data-history-day="2026-11-18"]').classList.contains('has-workout'), 'Time correction did not move the calendar marker');
  assert.equal(ui.main.querySelector('[data-history-day="2026-11-18"]').getAttribute('aria-pressed'), 'true', 'Time correction did not select the corrected day');
  assert(ui.main.querySelector('.history-session').textContent.includes('4h 30min'), 'History duration did not update after correcting timestamps');
}

async function checkTrackingRegressions(html, scripts) {
  const now = new Date(2026, 10, 9, 10).getTime();
  const store = fixture(() => now);
  const ui = harness(html, scripts, '', { now, window: { GYMROOK_STORE: store, confirm: () => true } });
  store.setClock(ui.now);
  await settle();
  const id = ui.data.workouts[0].blocks[0].exerciseIds[0];
  ui.document.getElementById('start-workout').click(); await settle();
  await openSeries(ui, id);

  // Invalid edits must block finalization without losing the draft or closing
  // the session using an older, silently substituted configuration.
  action(card(ui, id), 'edit').click(); await settle();
  input(card(ui, id), 'reps', 0).value = '-2';
  input(card(ui, id), 'reps', 0).dispatch('input');
  ui.location.hash = '#workout/A'; await settle();
  ui.document.getElementById('finish-workout').click(); await settle();
  assert(store.getActiveSession(), 'Invalid series must block workout finalization');
  await openSeries(ui, id);
  assert.equal(input(card(ui, id), 'reps', 0).value, '-2', 'Invalid draft was discarded while finalizing');
  assert(ui.document.getElementById('tracking-status').textContent.includes('inválidos'), 'Blocked finalization must explain the invalid fields');
  input(card(ui, id), 'reps', 0).value = '10';
  input(card(ui, id), 'reps', 0).dispatch('input');
  action(card(ui, id), 'done').click(); await settle();

  // A change event starts an asynchronous write. Navigation to progression
  // must wait for that write rather than displaying the preceding graph.
  const immediateUpdate = store.updateExercise.bind(store);
  let releaseWrite;
  const writeGate = new Promise(resolve => { releaseWrite = resolve; });
  store.updateExercise = (...args) => writeGate.then(() => immediateUpdate(...args));
  action(card(ui, id), 'edit').click(); await settle();
  input(card(ui, id), 'weight', 0).value = '23';
  input(card(ui, id), 'weight', 0).dispatch('change');
  ui.location.hash = '#progression/' + id;
  await settle();
  assert(!ui.main.querySelector('.history-chart-point'), 'Progression rendered before the outstanding edit was saved');
  releaseWrite(); await settle();
  assert(ui.main.querySelector('.history-chart-point')?.textContent.includes('23 kg'), 'Fast navigation rendered a stale progression value');
  store.updateExercise = immediateUpdate;

  // Model an import whose data replacement finishes before its promise settles.
  // Any earlier queued autosave must have been canceled before restoration starts.
  await openSeries(ui, id);
  action(card(ui, id), 'done').click(); await settle();
  action(card(ui, id), 'edit').click(); await settle();
  input(card(ui, id), 'weight', 0).value = '99';
  input(card(ui, id), 'weight', 0).dispatch('input');
  let lateWrites = 0;
  store.updateExercise = (...args) => { lateWrites++; return immediateUpdate(...args); };
  const restoreState = store.getState();
  restoreState.settings[id].weights = [7];
  restoreState.sessions[0].exercises[id].weights = [7];
  let releaseImport;
  const importGate = new Promise(resolve => { releaseImport = resolve; });
  const immediateImport = store.importBackup.bind(store);
  let enteredImport = false;
  store.importBackup = async json => { await immediateImport(json); enteredImport = true; await importGate; };
  ui.window.GYMROOK_TRACKING.renderBackup(ui.main);
  const importer = ui.main.querySelector('#backup-import');
  const json = JSON.stringify({app: 'GymRook', formatVersion: 1, exportedAt: new Date(now).toISOString(), state: restoreState});
  importer.files = [{name: 'restore.json', size: json.length, text: async () => json}];
  importer.dispatch('change'); await settle();
  assert(enteredImport, 'Import handler never began restoring the valid backup');
  ui.advance(300); await settle();
  assert.equal(lateWrites, 0, 'A queued autosave ran after backup restoration started');
  assert.deepEqual(store.getExercise(id).weights, [7], 'An old autosave overwrote restored load data');
  releaseImport(); await settle();
  assert.deepEqual(store.getExercise(id).weights, [7], 'Restored data changed after delayed import completion');

  // Failed storage initialization must explain the problem on all data screens,
  // while the exercise catalog remains consultable.
  const unavailable = fixture(() => now);
  unavailable.ready = Promise.reject(new Error('Storage denied for test'));
  const failed = harness(html, scripts, '#history', { now, window: { GYMROOK_STORE: unavailable, confirm: () => true } });
  await settle();
  assert(!failed.window.GYMROOK_TRACKING.isReady());
  assert(failed.main.textContent.includes('Não foi possível abrir'), 'Storage error left history indefinitely loading');
  failed.location.hash = '#progression'; await settle();
  assert(failed.main.textContent.includes('Não foi possível abrir'), 'Storage error left progression indefinitely loading');
  failed.location.hash = ''; await settle();
  assert.equal(failed.main.querySelectorAll('[data-exercise]').length, 10, 'Storage failure must not prevent catalog consultation');
}

async function checkDeletionScreens(html) {
  const scripts = await Promise.all(['data.js', 'history.js'].map(async name => [name, await read(name)]));
  const now = new Date(2026, 10, 23, 10).getTime();
  const store = fixture(() => now);
  let allow = false;
  const confirmations = [];
  const ui = harness(html, scripts, '', { now, window: { GYMROOK_STORE: store, confirm: text => { confirmations.push(text); return allow; } } });
  const id = ui.data.workouts[0].blocks[0].exerciseIds[0];
  const other = ui.data.workouts[0].blocks[1].exerciseIds[0];
  const iso = (date, hour = 10) => new Date(2026, 10, date, hour).toISOString();
  const points = [1, 8, 22].map((date, index) => ({exerciseId: id, date: `2026-11-${String(date).padStart(2, '0')}`, editedAt: iso(date), weights: [(index + 1) * 10], reps: [12 - index * 2, 10, 10]}));
  store.replace({schemaVersion: 1, updatedAt: iso(23), settings: {[id]: {weights: [30], reps: [8, 10, 10], updatedAt: iso(22)}, [other]: {weights: [55], reps: [9, 9], updatedAt: iso(22)}},
    sessions: ['one', 'two'].map((sessionId, index) => ({id: sessionId, workoutId: 'A', startedAt: iso(22, 10 + index), endedAt: new Date(2026, 10, 22, 10 + index, 30).toISOString(), restStartedAt: null,
      exercises: {[id]: {weights: [30], reps: [8, 10, 10], completed: [true, true, true]}}})),
    progression: [...points, {exerciseId: other, date: '2026-11-22', editedAt: iso(22), weights: [55], reps: [9, 9]}]});
  ui.window.GYMROOK_HISTORY.render(ui.main, '#history');
  const sessionDelete = () => ui.main.querySelector('[data-delete-session="two"]');
  assert(sessionDelete()?.querySelector('svg'), 'History delete action must use a trash SVG');
  sessionDelete().click(); await settle();
  assert.equal(store.getState().sessions.length, 2, 'Canceling history deletion changed saved sessions');
  assert(confirmations.at(-1).includes('A') && confirmations.at(-1).includes('22'), 'History confirmation must identify the concrete workout and day');
  allow = true;
  store.failNext(new Error('Falha ao excluir de teste'));
  sessionDelete().click(); await settle();
  assert.equal(store.getState().sessions.length, 2, 'Failed history deletion removed data');
  assert(ui.main.querySelector('.history-action-status').textContent.includes('Falha ao excluir'), 'History deletion failure was not shown');
  assert(!sessionDelete().disabled, 'Failed deletion left history action disabled');
  sessionDelete().click(); await settle();
  assert.equal(store.getState().sessions.length, 1);
  assert(ui.main.querySelector('[data-history-day="2026-11-22"]').classList.contains('has-workout'), 'Deleting one of two sessions cleared the whole trained day');
  assert.equal(ui.main.querySelectorAll('.history-session').length, 1);
  ui.main.querySelector('[data-delete-session="one"]').click(); await settle();
  assert.equal(store.getState().sessions.length, 0);
  assert(!ui.main.querySelector('[data-history-day="2026-11-22"]').classList.contains('has-workout'), 'Deleting the final session did not clear its calendar marker');
  assert.equal(store.getState().progression.length, 4, 'Deleting workout history must preserve load progression');

  ui.window.GYMROOK_HISTORY.render(ui.main, '#progression/' + id);
  let metric = ui.main.querySelector('#progression-metric'); metric.value = 'reps'; metric.dispatch('change');
  const progressionDelete = date => ui.main.querySelector(`[data-delete-progression="${date}"]`);
  assert(progressionDelete('2026-11-08')?.querySelector('svg'), 'Daily progression delete action must use a trash SVG');
  progressionDelete('2026-11-08').click(); await settle();
  assert.deepEqual(store.getExercise(id).weights, [30], 'Deleting a middle point changed current loads');
  assert.equal(ui.main.querySelectorAll('.history-chart-point').length, 2, 'Deleted middle point remains in chart');
  assert.equal(ui.main.querySelector('#progression-exercise').value, id, 'Deletion lost selected exercise');
  assert.equal(ui.main.querySelector('#progression-metric').value, 'reps', 'Deletion lost selected progression metric');
  allow = false;
  progressionDelete('2026-11-22').click(); await settle();
  assert.deepEqual(store.getExercise(id).weights, [30], 'Canceling latest progression deletion changed loads');
  assert(confirmations.at(-1).includes(ui.data.exercises[id].name), 'Progression confirmation must identify the exercise');
  allow = true; store.failNext(new Error('Progressão não excluída de teste'));
  progressionDelete('2026-11-22').click(); await settle();
  assert.deepEqual(store.getExercise(id).weights, [30]);
  assert(ui.main.querySelector('.history-action-status').textContent.includes('não excluída'), 'Progression deletion error was not shown');
  progressionDelete('2026-11-22').click(); await settle();
  assert.deepEqual(store.getExercise(id).weights, [10], 'Deleting latest point did not restore previous remaining load');
  assert.deepEqual(store.getExercise(id).reps, [12, 10, 10], 'Deleting latest point did not restore previous remaining reps');
  assert.equal(ui.main.querySelectorAll('.progression-day').length, 1);
  progressionDelete('2026-11-01').click(); await settle();
  assert.deepEqual(store.getExercise(id).weights, [], 'Deleting every point did not restore optional blank weights');
  assert.deepEqual(store.getExercise(id).reps, [10, 10, 10], 'Deleting every point did not restore default sets');
  assert.equal(ui.main.querySelectorAll('.history-chart-point').length, 0);
  assert(ui.main.textContent.includes('Ainda não há ajustes'), 'Empty progression state missing after last deletion');
  assert.deepEqual(store.getExercise(other).weights, [55], 'Progression deletion changed another exercise');
  assert.equal(store.getState().progression.filter(point => point.exerciseId === other).length, 1);
}

async function checkDeletedCurrentReturnsToDetail(html, scripts) {
  const now = new Date(2026, 10, 23, 10).getTime();
  const store = fixture(() => now);
  const ui = harness(html, scripts, '', {now, window: {GYMROOK_STORE: store, confirm: () => true}});
  await settle();
  const id = ui.data.workouts[0].blocks[0].exerciseIds[0];
  const previousAt = new Date(2026, 10, 22, 10).toISOString();
  store.replace({schemaVersion: 1, updatedAt: previousAt, settings: {[id]: {weights: [30], reps: [10, 10, 10], updatedAt: previousAt}}, sessions: [],
    progression: [{exerciseId: id, date: '2026-11-22', editedAt: previousAt, weights: [30], reps: [10, 10, 10]}]});
  await openSeries(ui, id);
  action(card(ui, id), 'edit').click(); await settle();
  input(card(ui, id), 'weight', 0).value = '40';
  input(card(ui, id), 'weight', 0).dispatch('change');
  await settle();
  ui.location.hash = '#progression/' + id; await settle();
  ui.main.querySelector('[data-delete-progression="2026-11-23"]').click(); await settle();
  assert.deepEqual(store.getExercise(id).weights, [30]);
  await openSeries(ui, id);
  const weightInput = card(ui, id).querySelector('[data-field="weight"]');
  if (weightInput) assert.equal(Number(weightInput.value.replace(',', '.')), 30, 'Returning to exercise detail must not show a deleted edit draft as the current load');
  else assert(card(ui, id).textContent.includes('30 kg'), 'Restored current load missing from exercise detail');
}

async function checkExerciseNotesAndCompletion(html, scripts) {
  const now = new Date(2026, 10, 18, 10).getTime();
  const store = fixture(() => now);
  const ui = harness(html, scripts, '', {now, window: {GYMROOK_STORE: store, confirm: () => true}});
  store.setClock(ui.now);
  await settle();
  const ids = ui.data.workouts[0].blocks.flatMap(block => block.exerciseIds);
  const id = ids[0], lastId = ids.at(-1);
  const progress = (scope, location = 'detail') => scope.main.querySelector(`[data-exercise-progress="${id}"][data-progress-location="${location}"]`);
  const checkCount = (node, completed, total) => assert(new RegExp(`${completed}\\s*(?:/|de)\\s*${total}`).test(node?.textContent || ''), `Missing completion summary ${completed}/${total}`);
  ui.document.getElementById('start-workout').click(); await settle();
  await openSeries(ui, id);
  checkCount(progress(ui), 0, 3);
  assert(!progress(ui).classList.contains('is-complete'));
  assert(!ui.main.querySelector('#finish-workout-top'), 'Top finish control must appear only on last exercise');

  const privateText = '<img src=x onerror="window.bad=true"> Banco 3\nAssento 2 & "controle"';
  const sessionText = 'Hoje: <script>window.bad=true</script>\nÚltima série sem impulso.';
  const privateInput = ui.main.querySelector('#exercise-private-note');
  const sessionInput = ui.main.querySelector('#exercise-session-note');
  assert(privateInput && sessionInput && !sessionInput.disabled, 'Exercise notes must provide fixed and active-session fields');
  privateInput.value = privateText; privateInput.dispatch('input');
  sessionInput.value = sessionText; sessionInput.dispatch('input');
  // Fast navigation flushes both note scopes rather than dropping their debounces.
  ui.location.hash = '#exercise/' + ids[1]; await settle();
  assert.equal(store.getExerciseNote(id), privateText, 'Navigation did not save private exercise note');
  assert.equal(store.getActiveSession().exercises[id].notes, sessionText, 'Navigation did not save session exercise note');
  assert.equal(store.getState().progression.length, 0, 'Note edits must not create load progression points');
  await openSeries(ui, id);
  assert.equal(ui.main.querySelector('#exercise-private-note').value, privateText);
  assert.equal(ui.main.querySelector('#exercise-session-note').value, sessionText);
  assert.equal(ui.main.querySelectorAll('script').length, 0, 'Exercise notes were interpreted as executable HTML');
  assert(!ui.main.querySelectorAll('img').some(image => image.getAttribute('src') === 'x'), 'Exercise note created an injected image');
  action(card(ui, id), 'complete').click(); await settle();
  checkCount(progress(ui), 1, 3);
  assert(!progress(ui).classList.contains('is-complete'), 'Partial completion must not turn summary green');
  for (let index = 1; index < 3; index++) { card(ui, id).querySelectorAll('[data-series-action="complete"]')[index].click(); await settle(); }
  checkCount(progress(ui), 3, 3);
  assert(progress(ui).classList.contains('is-complete'), 'Fully completed exercise summary must be complete');
  ui.location.hash = '#workout/A'; await settle();
  checkCount(progress(ui, 'list'), 3, 3);
  assert(ui.main.querySelector(`[data-exercise="${id}"]`).classList.contains('is-completed'), 'Workout list does not mark a completed exercise');
  assert(!ui.main.querySelector(`[data-exercise="${ids[1]}"]`).classList.contains('is-completed'), 'Untouched exercise inherited another exercise completion');

  const restored = harness(html, scripts, '#exercise/' + id, {now: ui.now(), window: {GYMROOK_STORE: store, confirm: () => true}});
  await settle();
  store.setClock(restored.now);
  checkCount(progress(restored), 3, 3);
  assert.equal(restored.main.querySelector('#exercise-private-note').value, privateText, 'Private note did not survive app reopening');
  assert.equal(restored.main.querySelector('#exercise-session-note').value, sessionText, 'Session note did not survive app reopening');

  const beforeNote = store.getExerciseNote(id);
  store.failNext(new Error('Falha de gravação da nota'));
  const failing = restored.main.querySelector('#exercise-private-note');
  failing.value = 'Rascunho ainda não salvo'; failing.dispatch('input');
  restored.advance(350); await settle();
  assert.equal(store.getExerciseNote(id), beforeNote, 'Failed note write changed saved data');
  assert(restored.document.getElementById('tracking-status').textContent.includes('Falha de gravação'), 'Failed note save needs a visible error');
  restored.advance(6000); await settle();
  assert(!restored.document.getElementById('tracking-status').hidden, 'Error toast disappeared before it was resolved');
  const retry = restored.main.querySelector('#exercise-private-note');
  retry.value = privateText; retry.dispatch('input');
  restored.advance(350); await settle();
  assert(restored.document.getElementById('tracking-status').hidden, 'Successful note retry must clear its persistent error without a saved banner');

  await openSeries(restored, lastId);
  const finish = restored.main.querySelector('#finish-workout-top');
  assert(finish, 'Last exercise must offer a top finish control');
  finish.click(); await settle();
  const dialog = restored.document.getElementById('finish-dialog');
  assert(dialog.open && store.getActiveSession(), 'Top finish must open confirmation before ending the workout');
  assert(dialog.getAttribute('aria-labelledby'), 'Finish dialog needs an accessible title');
  restored.document.dispatch('keydown', {key: 'Escape'});
  assert.equal(restored.location.hash, '#exercise/' + lastId, 'Escape from the finish dialog must not navigate away from the exercise');
  restored.document.getElementById('finish-cancel').click(); await settle();
  assert(!dialog.open && store.getActiveSession(), 'Canceling finish must keep session active');
  finish.click(); await settle();
  store.failNext(new Error('Não foi possível finalizar de teste'));
  restored.document.getElementById('finish-confirm').click(); await settle();
  assert(dialog.open && store.getActiveSession(), 'Failed finish must keep confirmation and session available');
  assert(restored.document.getElementById('finish-dialog-error').textContent.includes('finalizar'), 'Finish failure needs dialog feedback');
  restored.document.getElementById('finish-confirm').click(); await settle();
  assert(!dialog.open && !store.getActiveSession(), 'Confirming finish did not close the session/dialog');
  assert.equal(store.getState().sessions[0].exercises[id].notes, sessionText, 'Finishing dropped session notes');
  assert(restored.main.querySelector('.history-exercise-notes p').textContent.includes('<script>'), 'Session notes missing from history');
  restored.advance(5000); await settle();
  assert(restored.document.getElementById('tracking-status').hidden || !restored.document.getElementById('tracking-status').textContent, 'Success notification remained persistently visible');
  restored.location.hash = '#workout/A'; await settle();
  assert(!restored.main.querySelector(`[data-exercise="${id}"]`).classList.contains('is-completed'), 'Previous session completion stayed green after finishing');
  restored.document.getElementById('start-workout').click(); await settle();
  await openSeries(restored, id);
  checkCount(progress(restored), 0, 3);
  assert.equal(restored.main.querySelector('#exercise-session-note').value, '', 'New session reused the previous session note');
  assert.equal(restored.main.querySelector('#exercise-private-note').value, privateText, 'New session lost the fixed exercise note');
  assert(!progress(restored).classList.contains('is-complete'), 'New session inherited the previous session completion');
}

async function checkNoteImportRace(html, scripts) {
  const now = new Date(2026, 10, 18, 10).getTime();
  const store = fixture(() => now);
  const ui = harness(html, scripts, '', {now, window: {GYMROOK_STORE: store, confirm: () => true}});
  await settle();
  const id = ui.data.workouts[0].blocks[0].exerciseIds[0];
  ui.document.getElementById('start-workout').click(); await settle();
  await openSeries(ui, id);
  const restoredState = store.getState();
  restoredState.exerciseNotes[id] = 'Anotação fixa restaurada';
  restoredState.sessions[0].exercises[id].notes = 'Anotação da sessão restaurada';
  for (const selector of ['#exercise-private-note', '#exercise-session-note']) {
    const textarea = ui.main.querySelector(selector);
    textarea.value = 'Rascunho antigo ainda aguardando autosave'; textarea.dispatch('input');
  }
  let releaseImport;
  const gate = new Promise(resolve => { releaseImport = resolve; });
  const importNow = store.importBackup.bind(store);
  let replacing = false;
  store.importBackup = async json => { await importNow(json); replacing = true; await gate; };
  ui.window.GYMROOK_TRACKING.renderBackup(ui.main);
  const json = JSON.stringify({app: 'GymRook', formatVersion: 1, exportedAt: new Date(now).toISOString(), state: restoredState});
  const importer = ui.main.querySelector('#backup-import');
  importer.files = [{name: 'notes.json', size: json.length, text: async () => json}];
  importer.dispatch('change'); await settle();
  assert(replacing, 'Valid note backup import did not start');
  ui.advance(350); await settle();
  assert.equal(store.getExerciseNote(id), 'Anotação fixa restaurada', 'Queued private note overwrote imported backup');
  assert.equal(store.getActiveSession().exercises[id].notes, 'Anotação da sessão restaurada', 'Queued session note overwrote imported backup');
  releaseImport(); await settle();
  await openSeries(ui, id);
  assert.equal(ui.main.querySelector('#exercise-private-note').value, 'Anotação fixa restaurada', 'Private note draft was not reset after import');
  assert.equal(ui.main.querySelector('#exercise-session-note').value, 'Anotação da sessão restaurada', 'Session note draft was not reset after import');
}

async function checkSaveErrorRetries(html, scripts) {
  const now = new Date(2026, 10, 18, 10).getTime();
  const store = fixture(() => now);
  const ui = harness(html, scripts, '', {now, window: {GYMROOK_STORE: store, confirm: () => true}});
  await settle();
  ui.document.getElementById('start-workout').click(); await settle();
  const id = ui.data.workouts[0].blocks[0].exerciseIds[0];
  await openSeries(ui, id);
  store.failNext(new Error('Nota ainda pendente de gravação'));
  const note = ui.main.querySelector('#exercise-private-note');
  note.value = 'Anotação para nova tentativa'; note.dispatch('change'); await settle();
  assert(ui.document.getElementById('tracking-status').textContent.includes('Nota ainda pendente'));
  action(card(ui, id), 'edit').click(); await settle();
  const load = input(card(ui, id), 'weight', 0);
  store.failNext(new Error('Carga ainda pendente de gravação'));
  load.value = '30'; load.dispatch('change'); await settle();
  assert(ui.document.getElementById('tracking-status').textContent.includes('Carga ainda pendente'));
  action(card(ui, id), 'done').click(); await settle();
  assert.deepEqual(store.getExercise(id).weights, [30], 'Retry did not save the previously failed series load');
  const status = ui.document.getElementById('tracking-status');
  assert(!status.hidden && status.textContent.includes('Nota ainda pendente'), 'Successful series retry must preserve another pending write error');
  assert(!status.textContent.includes('Carga ainda pendente'), 'Successful series retry retained its resolved error');
  const retry = ui.main.querySelector('#exercise-private-note');
  retry.value = 'Anotação salva após nova tentativa'; retry.dispatch('change'); await settle();
  assert.equal(store.getExerciseNote(id), retry.value);
  assert(status.hidden && !status.textContent, 'Final successful retry must clear all resolved errors without a saved notice');
}

export async function checkTrackingUI() {
  const html = await read('index.html');
  await checkHistoryScreens(html);
  await checkSessionTimeEditing(html);
  await checkDeletionScreens(html);
  const names = ['data.js', 'anatomy.js', 'history.js', 'tracking.js', 'app.js'];
  const scripts = await Promise.all(names.map(async name => [name, await read(name)]));
  const scriptPaths = [...html.matchAll(/<script\b[^>]*\bsrc=["']([^"']+)["']/g)].map(match => match[1].replace(/^\.\//, ''));
  for (const name of ['store.js', 'history.js', 'tracking.js']) assert(scriptPaths.includes(name), `${name} must be included in offline app shell`);
  assert(scriptPaths.indexOf('store.js') < scriptPaths.indexOf('tracking.js') && scriptPaths.indexOf('tracking.js') < scriptPaths.indexOf('app.js'), 'Tracking script order is incorrect');
  await checkDeletedCurrentReturnsToDetail(html, scripts);
  await checkExerciseNotesAndCompletion(html, scripts);
  await checkNoteImportRace(html, scripts);
  await checkSaveErrorRetries(html, scripts);
  await checkTrackingRegressions(html, scripts);
  const initialNow = new Date(2026, 10, 9, 10, 0, 0).getTime();
  const store = fixture(() => initialNow);
  const downloads = [];
  const ui = harness(html, scripts, '', { now: initialNow, window: { GYMROOK_STORE: store, confirm: () => true }, globals: { URL: { createObjectURL(blob) { downloads.push(blob); return 'blob:test-backup'; }, revokeObjectURL() {} } } });
  store.setClock(ui.now);
  await store.ready; await settle();
  assert(ui.window.GYMROOK_TRACKING.isReady(), 'Tracking did not initialize');
  const firstId = ui.data.workouts[0].blocks[0].exerciseIds[0];
  assert(ui.document.getElementById('start-workout'), 'Workout start is missing');
  assert(ui.document.getElementById('start-workout').querySelector('svg'), 'Workout start must show a play SVG');
  assert(!store.getActiveSession(), 'Opening the guide must not start a workout');
  assert.equal(ui.main.querySelectorAll('[data-series-exercise]').length, 0, 'Workout listing must not contain series cards');
  for (const anchor of ui.main.querySelectorAll('[data-exercise]')) assert.equal(anchor.querySelectorAll('button').length + anchor.querySelectorAll('input').length, 0, 'Series controls must not be nested in catalog links');

  ui.document.getElementById('start-workout').click(); await settle();
  assert(ui.document.getElementById('finish-workout').querySelector('svg'), 'Workout finish must show a stop SVG');
  let session = store.getActiveSession();
  assert.equal(session.workoutId, 'A');
  assert.deepEqual(session.exercises[firstId].reps, [10, 10, 10], 'Initial configuration must be three sets of ten');
  assert.deepEqual(session.exercises[firstId].weights, [], 'No entered load must serialize as an empty array');
  const startedAt = session.startedAt;
  ui.advance(15000);
  assert(ui.document.getElementById('workout-clock').textContent.includes('00:15'), 'Workout timer did not advance');
  ui.document.getElementById('rest-toggle').click(); await settle();
  ui.advance(12000);
  assert(ui.document.getElementById('rest-clock').textContent.includes('00:12'), 'Rest timer did not advance');
  assert(ui.document.getElementById('workout-clock').textContent.includes('00:27'), 'Rest paused the total workout timer');
  ui.document.getElementById('rest-toggle').click(); await settle();
  assert.equal(store.getActiveSession().restStartedAt, null, 'Second rest press must reset rest');
  assert.equal(store.getActiveSession().startedAt, startedAt, 'Rest changed workout start');

  await openSeries(ui, firstId);
  let firstCard = card(ui, firstId);
  action(firstCard, 'complete').click(); await settle();
  assert.equal(store.getActiveSession().exercises[firstId].completed[0], true, 'Pressing a series must mark it complete');
  assert.equal(action(card(ui, firstId), 'complete').getAttribute('aria-pressed'), 'true', 'Completed series visual state is stale');
  action(card(ui, firstId), 'complete').click(); await settle();
  assert.equal(store.getActiveSession().exercises[firstId].completed[0], false, 'Second press must unmark completion');
  action(card(ui, firstId), 'edit').click(); await settle();
  firstCard = card(ui, firstId);
  assert.equal(firstCard.querySelectorAll('[data-field="reps"]').length, 3);
  input(firstCard, 'reps', 0).value = '12';
  input(firstCard, 'weight', 0).value = '12,5';
  input(firstCard, 'weight', 2).value = '15';
  input(firstCard, 'weight', 2).dispatch('input');
  action(firstCard, 'done').click(); await settle();
  assert.deepEqual(store.getExercise(firstId).weights, [12.5, null, 15], 'Loads must retain per-series alignment and allow blank series');
  assert.deepEqual(store.getExercise(firstId).reps, [12, 10, 10], 'Edited repetition counts were not saved');
  assert.equal(store.getState().progression.length, 1, 'First configuration edit must record progression');
  action(card(ui, firstId), 'edit').click(); await settle();
  action(card(ui, firstId), 'add').click(); await settle();
  assert.equal(store.getExercise(firstId).reps.length, 4, 'Adding a series failed');
  firstCard = card(ui, firstId);
  const lastRemove = firstCard.querySelectorAll('[data-series-action="remove"]').at(-1);
  lastRemove.click(); await settle();
  assert.equal(store.getExercise(firstId).reps.length, 3, 'Removing a series failed');
  action(card(ui, firstId), 'done').click(); await settle();
  assert.equal(store.getState().progression.length, 1, 'Multiple edits on same day must not add progression points');
  assert.equal(store.getActiveSession().exercises[firstId].reps.length, 3, 'Active session configuration must follow edits');
  for (let i = 0; i < 3; i++) {
    card(ui, firstId).querySelectorAll('[data-series-action="complete"]')[i].click(); await settle();
  }
  assert(store.getActiveSession().exercises[firstId].completed.every(Boolean));
  assert.equal(store.getState().progression.length, 1, 'Completion must not alter progression history');

  const secondId = ui.data.workouts[0].blocks[1].exerciseIds[0];
  await openSeries(ui, secondId);
  action(card(ui, secondId), 'edit').click(); await settle();
  input(card(ui, secondId), 'weight', 0).value = '0';
  input(card(ui, secondId), 'weight', 0).dispatch('input');
  action(card(ui, secondId), 'done').click(); await settle();
  assert.deepEqual(store.getExercise(secondId).weights, [0], 'Zero kg must remain a recorded load while trailing blanks are trimmed');
  assert(card(ui, secondId).textContent.includes('0 kg'), 'Zero kg must not display as missing load');
  action(card(ui, secondId), 'edit').click(); await settle();
  input(card(ui, secondId), 'weight', 0).value = '';
  input(card(ui, secondId), 'weight', 0).dispatch('input');
  action(card(ui, secondId), 'done').click(); await settle();
  assert.deepEqual(store.getExercise(secondId).weights, [], 'Clearing all loads must serialize as an empty array');
  assert.equal(store.getState().progression.filter(point => point.exerciseId === secondId).length, 1, 'Clearing load on same day must replace that day’s progression point');

  // A write failure must be visible and must leave the previous model intact.
  store.failNext(new Error('Disco sem espaço de teste'));
  ui.document.getElementById('rest-toggle').click(); await settle();
  assert.equal(store.getActiveSession().restStartedAt, null);
  assert(ui.document.getElementById('tracking-status').textContent.includes('Disco sem espaço'), 'Failed writes must be explained');
  assert(!ui.document.getElementById('rest-toggle').disabled, 'Failed write left the rest button stuck');

  // Navigation and a fresh app runtime both derive total time from persisted start.
  ui.location.hash = '#workout/A'; await settle();
  assert.equal(ui.main.querySelectorAll('[data-series-exercise]').length, 0, 'Active workout list must remain free of series cards');
  const tabB = ui.main.querySelectorAll('[role="tab"]').find(tab => tab.dataset.workout === 'B');
  tabB.click(); await settle();
  assert.equal(store.getActiveSession().workoutId, 'A', 'Browsing another workout must not switch the active session');
  assert(!ui.main.querySelector('#start-workout'), 'Another active session must prevent starting a second workout');
  ui.document.querySelector('.session-return').click(); await settle();
  assert.equal(ui.location.hash, '#workout/A', 'Sticky header did not link back to active workout');
  assert.equal(ui.main.querySelector('[role="tab"][aria-selected="true"]').dataset.workout, 'A', 'Returning to active workout selected the wrong tab');
  assert.equal(store.getState().sessions.length, 1);
  ui.location.hash = '#exercise/' + firstId; await settle();
  ui.advance(60000);
  assert(ui.document.getElementById('workout-clock').textContent.includes('01:27'), 'Catalog navigation reset the workout timer');
  const restoredNow = ui.now();
  const restored = harness(html, scripts, '#workout/A', { now: restoredNow, window: { GYMROOK_STORE: store, confirm: () => true } });
  await settle();
  assert(restored.document.getElementById('workout-clock').textContent.includes('01:27'), 'Reopening runtime did not restore elapsed time');
  assert.equal(store.getActiveSession().startedAt, startedAt);
  await openSeries(restored, firstId);
  assert.equal(action(card(restored, firstId), 'complete').getAttribute('aria-pressed'), 'true', 'Completion did not survive reopening runtime');
  store.setClock(restored.now);
  restored.advance(33000);
  restored.location.hash = '#workout/A'; await settle();
  restored.document.getElementById('finish-workout').click(); await settle();
  assert.equal(store.getActiveSession(), null, 'Finishing did not close active session');
  assert.equal(store.getState().sessions.length, 1, 'Finishing invented extra sessions');
  assert.equal(restored.location.hash, '#history', 'Finish must open history');
  assert(restored.document.getElementById('session-header').hidden, 'Finished workout left header running');
  const saved = store.getState().sessions[0];
  assert.equal(new Date(saved.endedAt) - new Date(saved.startedAt), 120000, 'Total duration must include rest and closed-screen elapsed time');
  assert.equal(restored.main.querySelectorAll('.history-session').length, 1, 'Finished session is missing from history');
  assert(restored.main.textContent.includes('1 de 10'), 'History must report fully completed exercise count');

  ui.location.hash = '#backup'; await settle();
  assert(!/Backup diário|Arquivo vinculado|cópia diária/i.test(ui.main.textContent), 'Manual backup screen must not offer automatic backup');
  assert(!ui.main.querySelector('#backup-connect') && !ui.main.querySelector('#backup-daily'), 'Removed backup actions must not remain');
  for (const word of ['séries', 'progressão', 'cópia', 'restauração']) assert(ui.main.textContent.includes(word), `Manual backup text must preserve UTF-8 accents in ${word}`);
  ui.main.querySelector('#backup-export').click(); await settle();
  assert.equal(downloads.length, 1, 'Export did not prepare exactly one JSON download');
  const exported = JSON.parse(await downloads[0].text());
  assert.equal(exported.app, 'GymRook');
  assert.equal(exported.state.sessions.length, 1);
  const previousState = store.getState();
  const importer = ui.main.querySelector('#backup-import');
  importer.files = [{name: 'bad.json', size: 2, text: async () => '{}'}]; importer.dispatch('change'); await settle();
  assert(ui.main.querySelector('#backup-import-status').textContent.includes('não é um backup'), 'Invalid backup import is not explained');
  assert.deepEqual(store.getState(), previousState, 'Invalid import modified existing data');
  console.log('Tracking UI: summaries, private/session notes, time correction, confirmed finish, timers, calendar/progression, deletion rollback, autosave/import races and errors passed (in-memory DOM; no browser/layout test).');
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  try { await checkTrackingUI(); }
  catch (error) { console.error(error.stack || error); process.exitCode = 1; }
}
