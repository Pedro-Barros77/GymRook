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
        put(value, key) { pending.push(() => { working.set(key, clone(value)); }); }
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

function harness({idb = memoryIndexedDB(), opfs = true, picker = false, initialTime = '2026-11-08T15:00:00.000Z'} = {}) {
  let time = Date.parse(initialTime);
  const events = new Map();
  const files = new Map();
  const fileWrites = [];
  let externalPermission = 'granted';
  let fileFailure = false;
  let externalJson = null;
  class Clock extends Date {
    constructor(...args) { super(...(args.length ? args : [time])); }
    static now() { return time; }
  }
  const handle = name => ({testHandle: true,
    async queryPermission() { return externalPermission; },
    async requestPermission() { return externalPermission; },
    async createWritable() {
      let buffered;
      return {
        async write(json) { if (fileFailure) throw new Error('Disk error'); buffered = json; },
        async close() { if (name === 'external') externalJson = buffered; else files.set(name, buffered); fileWrites.push({name, json: buffered}); },
        async abort() {}
      };
    }
  });
  const window = {indexedDB: idb, addEventListener(name, callback) { events.set(name, callback); }};
  if (picker) window.showSaveFilePicker = async () => handle('external');
  const context = vm.createContext({window, navigator: {storage: {
    persist: async () => true,
    ...(opfs ? {getDirectory: async () => ({getFileHandle: async name => handle(name)})} : {})
  }}, Date: Clock, crypto: {randomUUID: () => `test-${time}-${Math.random()}`}, console, setTimeout});
  vm.runInContext(catalogSource, context);
  vm.runInContext(source, context);
  return {
    store: window.GYMROOK_STORE, idb, files, fileWrites,
    setTime(value) { time = Date.parse(value); },
    setPermission(value) { externalPermission = value; },
    failFile(value = true) { fileFailure = value; },
    externalJson: () => externalJson,
    focus: () => events.get('focus')?.()
  };
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
  assert.equal(await store.getDailyBackup(), null, 'Opening the catalog does not create or download a backup');
  let changes = 0;
  const unsubscribe = store.subscribe(() => changes++);
  await store.startSession('A', [id]);
  const startedAt = store.getActiveSession().startedAt;
  assert.equal(store.backupStatus().storage, 'opfs');
  assert.equal(h.files.size, 1);
  assert.equal(JSON.parse(h.files.get('gymrook-backup.json')).state.sessions.length, 1);
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
  assert.equal(store.backupStatus().date, '2026-11-22');
  assert.equal(h.files.size, 1, 'Daily updates overwrite one file instead of accumulating files');
  assert.equal([...h.idb.records.keys()].filter(key => key === 'daily-backup').length, 1);
  const reopened = harness({idb: h.idb});
  await reopened.store.ready;
  assert.deepEqual(plain(reopened.store.getActiveSession()), plain(store.getActiveSession()), 'An active session survives a page reload');
  await store.finishSession();
  const ended = store.getState().sessions[0];
  assert.equal(store.getActiveSession(), null);
  assert.equal(ended.endedAt, '2026-11-22T15:00:00.000Z');
  assert.equal(ended.restStartedAt, null);
  assert.equal(JSON.parse(await store.getDailyBackup()).state.sessions[0].endedAt, ended.endedAt, 'Finishing on a later day refreshes the snapshot with the final end time');
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
  const imported = harness({opfs: false});
  await imported.store.ready;
  await imported.store.importBackup(json);
  assert.deepEqual(plain(imported.store.getState().sessions), plain(store.getState().sessions));
  assert.equal(imported.store.backupStatus().storage, 'indexeddb', 'Unavailable OPFS falls back to an independent IDB snapshot');
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
  const left = harness({idb: crossTabs, opfs: false});
  const right = harness({idb: crossTabs, opfs: false});
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
  const dailyCombined = JSON.parse(await left.store.getDailyBackup()).state;
  assert.equal(dailyCombined.settings[id].weights[0], 11);
  assert.equal(dailyCombined.settings['pec-deck'].weights[0], 21, 'Backup lease fallback serializes snapshots from concurrent tabs');
  const external = harness({picker: true});
  await external.store.ready;
  await external.store.connectBackupFile();
  assert.equal(external.store.backupStatus().externalPermission, 'granted');
  assert.equal(JSON.parse(external.externalJson()).app, 'GymRook');
  external.setPermission('prompt');
  await external.store.startSession('A', [id]);
  assert.equal(external.store.backupStatus().externalPermission, 'prompt');
  assert.match(external.store.backupStatus().error, /autorizar/);
  external.setPermission('granted');
  await external.store.requestBackupPermission();
  assert.equal(JSON.parse(external.externalJson()).state.sessions.length, 1);
  external.failFile();
  const oldPrivateFile = external.files.get('gymrook-backup.json');
  await external.store.toggleSet(id, 0);
  assert.equal(external.store.getActiveSession().exercises[id].completed[0], true, 'An external-file failure must not discard a durable workout');
  assert.equal(external.store.backupStatus().storage, 'indexeddb');
  assert.match(external.store.backupStatus().error, /arquivo vinculado/);
  assert.equal(external.files.get('gymrook-backup.json'), oldPrivateFile, 'A failed file write preserves the prior complete private file');
  assert(JSON.parse(await external.store.getDailyBackup()).state.sessions[0].exercises[id].completed[0]);
  const linkedDB = memoryIndexedDB();
  const linkA = harness({idb: linkedDB, picker: true});
  await linkA.store.ready;
  await linkA.store.connectBackupFile();
  const linkB = harness({idb: linkedDB, picker: true});
  await linkB.store.ready;
  await linkB.store.connectBackupFile();
  const previousA = linkA.externalJson();
  await linkA.store.startSession('A', [id]);
  assert.equal(linkA.externalJson(), previousA, 'An older tab does not keep writing a previously linked file');
  assert.equal(JSON.parse(linkB.externalJson()).state.sessions.length, 1, 'Each backup rereads the current linked handle chosen by another tab');
  linkA.focus();
  await tick();
  const recoveredDB = memoryIndexedDB();
  const brokenState = {...plain(payload.state), sessions: 'corrupted'};
  recoveredDB.records.set('state', brokenState);
  recoveredDB.records.set('daily-backup', {json, date: '2026-11-22', updatedAt: '2026-11-22T15:00:00.000Z', storage: 'indexeddb'});
  const recovery = harness({idb: recoveredDB, opfs: false});
  await assert.rejects(recovery.store.ready, /Formato/);
  assert.equal(recovery.store.canRestore(), true, 'An open database permits recovery even when its state is malformed');
  assert.match(recovery.store.getInitializationError(), /Formato/);
  assert.equal(recovery.store.backupStatus().date, '2026-11-22', 'Daily backup metadata remains visible in recovery mode');
  assert.equal(await recovery.store.getDailyBackup(), json);
  await assert.rejects(recovery.store.importBackup('{bad'), /JSON/);
  assert.deepEqual(recoveredDB.records.get('state'), brokenState, 'A failed recovery import preserves the original record');
  await recovery.store.importBackup(json);
  assert.equal(recovery.store.getInitializationError(), null);
  assert.deepEqual(plain(recovery.store.getState().sessions), payload.state.sessions, 'A fully validated backup replaces malformed state atomically');
  await assert.rejects(h.store.connectBackupFile(), /não permite vincular/);
  unsubscribe();
  assert(changes > 0);
  console.log('Store: persistent sessions, rest, series, daily backup, imports, file permissions and concurrent transactions passed.');
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) await checkStore();
