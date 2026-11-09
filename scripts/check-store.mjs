import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import vm from 'node:vm';

const source = await readFile(new URL('../dist/store.js', import.meta.url), 'utf8');
const catalogSource = await readFile(new URL('../dist/data.js', import.meta.url), 'utf8');
const tick = () => new Promise(resolve => setImmediate(resolve));
const plain = value => JSON.parse(JSON.stringify(value));

// Transactional test double: whole transactions are serialized and writes are
// committed only on success, including concurrent callers in different VMs.
// This checks the model's transaction boundaries, not browser IDB implementation.
function memoryIndexedDB() {
  const records = new Map();
  let tail = Promise.resolve();
  let failNextCommit = false;
  const clone = value => value?.testHandle ? value : structuredClone(value);
  const database = {
    objectStoreNames: {contains: () => true},
    createObjectStore() {}, close() {},
    transaction(name, mode) {
      assert.equal(name, 'records');
      const pending = [];
      const tx = {error: null, aborted: false, abort() { this.aborted = true; }};
      let working;
      tx.objectStore = () => ({
        get(key) {
          const request = {};
          pending.push(() => { request.result = clone(working.get(key)); request.onsuccess?.(); });
          return request;
        },
        put(value, key) { pending.push(() => { working.set(key, clone(value)); }); },
        delete(key) { pending.push(() => { working.delete(key); }); }
      });
      const run = async () => {
        working = new Map([...records].map(([key, value]) => [key, clone(value)]));
        await tick();
        while (pending.length && !tx.aborted) { pending.shift()(); await tick(); }
        if (mode === 'readwrite' && failNextCommit) { failNextCommit = false; tx.error = new Error('Injected quota failure'); tx.aborted = true; }
        if (tx.aborted) { tx.onabort?.(); return; }
        if (mode === 'readwrite') { records.clear(); for (const entry of working) records.set(...entry); }
        tx.oncomplete?.();
      };
      tail = tail.then(run);
      return tx;
    }
  };
  return {
    records,
    failWrite() { failNextCommit = true; },
    open() { const request = {result: database}; setImmediate(() => request.onsuccess?.()); return request; }
  };
}

function harness({idb = memoryIndexedDB(), initialTime = '2026-11-08T15:00:00.000Z', initialFiles = []} = {}) {
  let time = Date.parse(initialTime);
  const events = new Map();
  const files = new Map(initialFiles);
  const calls = {directory: 0, removed: [], picker: 0, writable: 0};
  class Clock extends Date {
    constructor(...args) { super(...(args.length ? args : [time])); }
    static now() { return time; }
  }
  const window = {
    indexedDB: idb,
    addEventListener(name, callback) { events.set(name, callback); },
    showSaveFilePicker() { calls.picker++; throw new Error('Unexpected file picker'); }
  };
  const context = vm.createContext({window, navigator: {storage: {
    persist: async () => true,
    getDirectory: async () => {
      calls.directory++;
      return {
        async removeEntry(name) { calls.removed.push(name); files.delete(name); },
        async getFileHandle() { calls.writable++; throw new Error('Unexpected automatic file write'); }
      };
    }
  }}, Date: Clock, crypto: {randomUUID: () => `test-${time}-${Math.random()}`}, console});
  vm.runInContext(catalogSource, context);
  vm.runInContext(source, context);
  return {
    store: window.GYMROOK_STORE, idb, files, calls,
    setTime(value) { time = Date.parse(value); },
    focus: () => events.get('focus')?.()
  };
}

async function checkDeletions() {
  const h = harness({initialTime: '2026-11-01T15:00:00.000Z'});
  const store = h.store;
  const id = 'incline-dumbbell-press';
  const other = 'pec-deck';
  await store.ready;
  await store.updateExercise(id, {weights: [10, 20, 30], reps: [10, 10, 10]});
  await store.startSession('A', [id]);
  await store.toggleSet(id, 0);
  const first = await store.finishSession();
  await store.startSession('A', [id]);
  const second = await store.finishSession();
  assert.equal(store.getState().sessions.filter(session => session.startedAt.slice(0, 10) === '2026-11-01').length, 2);
  h.setTime('2026-11-08T15:00:00.000Z');
  await store.updateExercise(id, {weights: [12, 22, 32], reps: [10, 10, 10]});
  h.setTime('2026-11-15T15:00:00.000Z');
  await store.updateExercise(id, {weights: [16, 24, 36], reps: [10, 10, 10]});
  h.setTime('2026-11-22T15:00:00.000Z');
  await store.updateExercise(id, {weights: [16, 26, 36], reps: [10, 10, 10]});
  await store.updateExercise(other, {weights: [40], reps: [12]});
  await store.startSession('A', [id]);
  for (const index of [0, 1, 2]) await store.toggleSet(id, index);
  const activeId = store.getActiveSession().id;
  const finishedSnapshots = plain(store.getState().sessions.filter(session => session.endedAt));
  const unrelatedSettings = plain(store.getExercise(other));
  const unrelatedProgression = plain(store.getState().progression.filter(point => point.exerciseId === other));
  await store.deleteProgression(id, '2026-11-08');
  assert.deepEqual(plain(store.getExercise(id).weights), [16, 26, 36], 'Removing a middle point preserves the latest configuration');
  assert.deepEqual(plain(store.getActiveSession().exercises[id].completed), [true, true, true]);
  await store.deleteProgression(id, '2026-11-01');
  assert.deepEqual(plain(store.getExercise(id).weights), [16, 26, 36], 'Removing the oldest point preserves the latest configuration');
  await store.deleteProgression(id, '2026-11-22');
  assert.deepEqual(plain(store.getExercise(id).weights), [16, 24, 36], 'Removing the latest point restores the preceding configuration');
  assert.equal(store.getExercise(id).updatedAt, '2026-11-15T15:00:00.000Z');
  assert.deepEqual(plain(store.getActiveSession().exercises[id].completed), [true, false, true], 'Only active sets whose restored values change lose completion');
  assert.deepEqual(plain(store.getState().sessions.filter(session => session.endedAt)), finishedSnapshots, 'Progression deletion never rewrites finished workout snapshots');
  await store.deleteProgression(id, '2026-11-15');
  assert.deepEqual(plain(store.getExercise(id)), {weights: [], reps: [10, 10, 10], updatedAt: null}, 'Removing all points restores default sets and no load');
  assert.deepEqual(plain(store.getActiveSession().exercises[id].weights), []);
  assert.equal(store.getState().progression.filter(point => point.exerciseId === id).length, 0, 'Deletion does not create a new point for today');
  assert.deepEqual(plain(store.getExercise(other)), unrelatedSettings);
  assert.deepEqual(plain(store.getState().progression.filter(point => point.exerciseId === other)), unrelatedProgression);
  await assert.rejects(store.deleteProgression(id, '2026-11-15'), /não encontrado/);
  await assert.rejects(store.deleteProgression(id, '2026-02-30'), /Data de edição inválida/);
  await assert.rejects(store.deleteProgression('unknown', '2026-11-15'), /não encontrado/);
  await assert.rejects(store.deleteSession(activeId), /em andamento/);
  const beforeSessionDeletion = plain(store.getState());
  await store.deleteSession(first.id);
  assert.equal(store.getState().sessions.filter(session => session.startedAt.slice(0, 10) === '2026-11-01').length, 1, 'Removing one workout retains another workout on the same calendar day');
  assert(store.getState().sessions.some(session => session.id === second.id));
  assert.deepEqual(plain(store.getState().settings), beforeSessionDeletion.settings);
  assert.deepEqual(plain(store.getState().progression), beforeSessionDeletion.progression);
  await assert.rejects(store.deleteSession(first.id), /não encontrado/);
  await assert.rejects(store.deleteSession(''), /inválido/);
  const reopened = harness({idb: h.idb});
  await reopened.store.ready;
  assert.deepEqual(plain(reopened.store.getState()), plain(store.getState()), 'Deleted records and restored configuration survive reload');
  h.setTime('2026-11-30T15:00:00.000Z');
  await store.updateExercise(id, {weights: [18], reps: [8]});
  const beforeFailure = plain(store.getState());
  h.idb.failWrite();
  await assert.rejects(store.deleteProgression(id, '2026-11-30'), /quota/);
  assert.deepEqual(plain(store.getState()), beforeFailure, 'A failed point deletion preserves both the point and active configuration');
  assert.deepEqual(h.idb.records.get('state'), beforeFailure);
  h.idb.failWrite();
  await assert.rejects(store.deleteSession(second.id), /quota/);
  assert.deepEqual(plain(store.getState()), beforeFailure, 'A failed workout deletion preserves the completed session');
  const concurrent = harness({idb: h.idb});
  await concurrent.store.ready;
  await Promise.all([
    store.deleteProgression(id, '2026-11-30'),
    concurrent.store.updateExercise(other, {weights: [66], reps: [12]})
  ]);
  const merged = JSON.parse(await store.exportBackup()).state;
  assert.equal(merged.settings[other].weights[0], 66, 'A concurrent edit to another exercise survives point deletion');
  assert.equal(merged.progression.some(point => point.exerciseId === id), false);
  assert.deepEqual(plain(merged.sessions.find(session => !session.endedAt).exercises[id].weights), []);
  await Promise.all([
    store.deleteSession(second.id),
    concurrent.store.updateExercise(other, {weights: [68], reps: [12]})
  ]);
  const mergedSessions = JSON.parse(await store.exportBackup()).state;
  assert.equal(mergedSessions.sessions.some(session => session.id === second.id), false);
  assert.equal(mergedSessions.settings[other].weights[0], 68, 'Concurrent workout deletion preserves other exercise edits');
}

export async function checkStore() {
  const h = harness();
  const store = h.store;
  await store.ready;
  const id = 'incline-dumbbell-press';
  assert.deepEqual(plain(store.getExercise(id).reps), [10, 10, 10]);
  assert.deepEqual(plain(store.getExercise(id).weights), []);
  await store.updateExercise(id, {weights: [null, null, null], reps: [10, 10, 10]});
  assert.equal(store.getState().progression.length, 0, 'Confirming unchanged default sets does not create an editing day');
  assert.equal(store.getExercise(id).updatedAt, null);
  let changes = 0;
  const unsubscribe = store.subscribe(() => changes++);
  await store.startSession('A', [id]);
  const startedAt = store.getActiveSession().startedAt;
  await assert.rejects(store.startSession('B'), /em andamento/);
  h.setTime('2026-11-08T15:02:00.000Z');
  await store.toggleRest();
  assert.equal(store.getActiveSession().restStartedAt, '2026-11-08T15:02:00.000Z');
  assert.equal(store.getActiveSession().startedAt, startedAt, 'Rest does not change the workout clock');
  await store.toggleRest();
  assert.equal(store.getActiveSession().restStartedAt, null);
  await store.updateExercise(id, {weights: [12, 14, null], reps: [10, 10, 8]});
  assert.deepEqual(plain(store.getExercise(id).weights), [12, 14], 'Blank trailing loads are omitted');
  await store.toggleSet(id, 0);
  await store.toggleSet(id, 1);
  await store.updateExercise(id, {weights: [12, 16], reps: [10, 10, 8]});
  assert.deepEqual(plain(store.getActiveSession().exercises[id].completed), [true, false, false], 'Editing a completed set invalidates only the changed set');
  assert.equal(store.getState().progression.length, 1, 'Multiple edits on one day produce one point');
  h.setTime('2026-11-22T15:00:00.000Z');
  const previousEdit = store.getExercise(id).updatedAt;
  await store.updateExercise(id, {weights: [12, 16, null], reps: [10, 10, 8]});
  assert.equal(store.getState().progression.length, 1, 'Confirming identical sets on a later date does not add a graph point');
  assert.equal(store.getExercise(id).updatedAt, previousEdit, 'An unchanged configuration retains its editing timestamp');
  await store.updateExercise(id, {weights: [null, 18], reps: [12, 8]});
  assert.deepEqual(plain(store.getExercise(id).weights), [null, 18], 'Unweighted sets keep the alignment of later loads');
  assert.equal(store.getState().progression.length, 2, 'A later editing day adds a point');
  const reopened = harness({idb: h.idb});
  await reopened.store.ready;
  assert.deepEqual(plain(reopened.store.getActiveSession()), plain(store.getActiveSession()), 'An active session survives a page reload');
  await store.finishSession();
  const ended = store.getState().sessions[0];
  assert.equal(store.getActiveSession(), null);
  assert.equal(ended.endedAt, '2026-11-22T15:00:00.000Z');
  assert.equal(ended.restStartedAt, null);
  await assert.rejects(store.toggleSet(id, 0), /Inicie/);
  await assert.rejects(store.updateExercise(id, {weights: [-1], reps: [10]}), /carga/);
  await assert.rejects(store.updateExercise(id, {weights: [1, 2], reps: [10]}), /Séries/);
  await assert.rejects(store.updateExercise(id, {weights: [], reps: [1.5]}), /repetições/);
  await assert.rejects(store.updateExercise(id, {weights: [], reps: Array(31).fill(10)}), /30 séries/);
  await assert.rejects(store.updateExercise(id, {weights: [10001], reps: [10]}), /carga/);
  await assert.rejects(store.updateExercise('unknown-exercise', {weights: [], reps: []}), /não encontrado/);
  const beforeFailure = plain(store.getState());
  h.idb.failWrite();
  await assert.rejects(store.updateExercise(id, {weights: [30], reps: [10]}), /quota/);
  assert.deepEqual(plain(store.getState()), beforeFailure, 'Failed commits do not claim an in-memory success');
  const json = await store.exportBackup();
  const payload = JSON.parse(json);
  const imported = harness();
  await imported.store.ready;
  await imported.store.importBackup(json);
  assert.deepEqual(plain(imported.store.getState().sessions), plain(store.getState().sessions));
  const beforeInvalidImport = plain(imported.store.getState());
  await assert.rejects(imported.store.importBackup('{bad'), /JSON/);
  const invalid = plain(payload);
  invalid.state.progression[0].weights = [-2];
  assert.throws(() => imported.store.validateBackup(JSON.stringify(invalid)), /carga/, 'Full validation is available before a UI replaces pending edits');
  await assert.rejects(imported.store.importBackup(JSON.stringify(invalid)), /carga/);
  assert.deepEqual(plain(imported.store.getState()), beforeInvalidImport, 'Invalid imports cannot replace good data');
  const dupe = plain(payload);
  dupe.state.sessions.push(plain(dupe.state.sessions[0]));
  await assert.rejects(imported.store.importBackup(JSON.stringify(dupe)), /Treino inválido/);
  const crossTabs = memoryIndexedDB();
  const left = harness({idb: crossTabs});
  const right = harness({idb: crossTabs});
  await Promise.all([left.store.ready, right.store.ready]);
  await Promise.all([
    left.store.updateExercise(id, {weights: [10], reps: [10]}),
    right.store.updateExercise('pec-deck', {weights: [20], reps: [12]})
  ]);
  const combined = JSON.parse(await left.store.exportBackup()).state;
  assert(combined.settings[id] && combined.settings['pec-deck'], 'Concurrent tabs read/modify/write atomically without losing other exercises');
  await left.store.startSession('A', [id]);
  await Promise.all([
    left.store.updateExercise(id, {weights: [11], reps: [10]}),
    right.store.updateExercise('pec-deck', {weights: [21], reps: [12]})
  ]);
  const combinedSession = JSON.parse(await left.store.exportBackup()).state;
  assert.equal(combinedSession.settings[id].weights[0], 11);
  assert.equal(combinedSession.settings['pec-deck'].weights[0], 21);
  assert.equal(combinedSession.sessions.length, 1);
  assert.deepEqual([...h.idb.records.keys()], ['state'], 'Workout edits and timers keep only the primary state, with no automatic snapshots');
  assert.equal(h.calls.directory, 0, 'Fresh profiles never access the private file system');
  assert.equal(h.calls.picker, 0, 'Workout actions never open a file picker');
  assert.equal(h.calls.writable, 0, 'Workout actions never write automatic backup files');
  assert.deepEqual([...imported.idb.records.keys()], ['state'], 'Manual import does not create an automatic backup');
  const legacyDB = memoryIndexedDB();
  const originalState = plain(payload.state);
  let externalCalls = 0;
  legacyDB.records.set('state', originalState);
  legacyDB.records.set('daily-backup', {json});
  legacyDB.records.set('backup-meta', {externalDate: '2026-11-22'});
  legacyDB.records.set('external-file', {testHandle: true, createWritable() { externalCalls++; throw new Error('User file must remain untouched'); }, queryPermission() { externalCalls++; }});
  legacyDB.records.set('backup-lease', null);
  legacyDB.records.set('unrelated-record', {keep: true});
  const legacy = harness({idb: legacyDB, initialFiles: [['gymrook-backup.json', json], ['unrelated.json', 'keep']]});
  await legacy.store.ready;
  assert.deepEqual(plain(legacy.store.getState()), originalState, 'Removing obsolete backup copies preserves every existing workout record');
  assert.deepEqual([...legacyDB.records.keys()], ['state', 'unrelated-record']);
  assert.deepEqual(legacy.calls.removed, ['gymrook-backup.json'], 'Migration removes only the owned obsolete private file');
  assert.equal(legacy.files.get('unrelated.json'), 'keep');
  assert.equal(externalCalls, 0, 'The previously linked user file is never queried, written or deleted');
  const migrated = harness({idb: legacyDB});
  await migrated.store.ready;
  assert.equal(migrated.calls.directory, 0, 'Legacy cleanup is not repeated after obsolete records are gone');
  const recoveredDB = memoryIndexedDB();
  const brokenState = {...plain(payload.state), sessions: 'corrupted'};
  recoveredDB.records.set('state', brokenState);
  const recovery = harness({idb: recoveredDB});
  await assert.rejects(recovery.store.ready, /Formato/);
  assert.equal(recovery.store.canRestore(), true, 'An open database permits recovery even when its state is malformed');
  assert.match(recovery.store.getInitializationError(), /Formato/);
  await assert.rejects(recovery.store.importBackup('{bad'), /JSON/);
  assert.deepEqual(recoveredDB.records.get('state'), brokenState, 'A failed recovery import preserves the original record');
  await recovery.store.importBackup(json);
  assert.equal(recovery.store.getInitializationError(), null);
  assert.deepEqual(plain(recovery.store.getState().sessions), payload.state.sessions, 'A fully validated backup replaces malformed state atomically');
  unsubscribe();
  assert(changes > 0);
  await checkDeletions();
  console.log('Store: persistent sessions, rest, series, manual export/import, deletion, legacy cleanup and concurrent transactions passed.');
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) await checkStore();
