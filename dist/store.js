/* Personal workout records stay on this device. No network requests or accounts. */
(() => {
  'use strict';
  const DB_NAME = 'gymrook-personal';
  const DB_VERSION = 1;
  const TABLE = 'records';
  const BACKUP_FILE = 'gymrook-backup.json';
  const MAX_SETS = 30;
  const MAX_RECORDS = 50000;
  const validExercises = new Set(Object.keys(window.GYMROOK_DATA?.exercises || {}));
  const workoutIds = new Set((window.GYMROOK_DATA?.workouts || []).map(workout => workout.id));
  const listeners = new Set();
  const copy = value => JSON.parse(JSON.stringify(value));
  const now = () => new Date().toISOString();
  const localDate = value => {
    const date = value ? new Date(value) : new Date();
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  };
  const blankState = () => ({schemaVersion: 1, updatedAt: now(), settings: {}, sessions: [], progression: []});
  const defaults = () => ({weights: [], reps: [10, 10, 10], updatedAt: null});
  let state = blankState();
  let database;
  let queue = Promise.resolve();
  let externalFile = null;
  let channel = null;
  let initializationError = null;
  let backup = {date: null, updatedAt: null, storage: null, externalSupported: typeof window.showSaveFilePicker === 'function', externalConnected: false, externalPermission: 'unavailable', externalDate: null, externalUpdatedAt: null, error: null};

  function notify() { for (const listener of listeners) { try { listener(); } catch (error) { console.error(error); } } }
  function object(value) { return value && typeof value === 'object' && !Array.isArray(value); }
  function fail(message) { throw new Error(message); }
  function exerciseId(id) { if (!validExercises.has(id)) fail('Exercício não encontrado.'); return id; }
  function timestamp(value, nullable = false) {
    if (value == null && nullable) return null;
    if (typeof value !== 'string' || !Number.isFinite(Date.parse(value))) fail('Data inválida no backup.');
    return new Date(value).toISOString();
  }
  function day(value) {
    if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value) || new Date(`${value}T12:00:00`).getFullYear() < 2000 || localDate(`${value}T12:00:00`) !== value) fail('Dia inválido no backup.');
    return value;
  }
  function series(value) {
    if (!object(value) || !Array.isArray(value.reps) || !Array.isArray(value.weights) || value.reps.length > MAX_SETS || value.weights.length > value.reps.length) fail('Séries inválidas. Use até 30 séries por exercício.');
    const reps = value.reps.map(number => {
      if (!Number.isInteger(number) || number < 0 || number > 10000) fail('Informe repetições entre 0 e 10000.');
      return number;
    });
    const weights = value.weights.map(number => {
      if (number === null) return null;
      if (typeof number !== 'number' || !Number.isFinite(number) || number < 0 || number > 10000) fail('Informe uma carga entre 0 e 10000 kg.');
      return Math.round(number * 1000) / 1000;
    });
    while (weights.length && weights[weights.length - 1] === null) weights.pop();
    return {weights, reps};
  }
  function validateState(input) {
    if (!object(input) || input.schemaVersion !== 1 || !object(input.settings) || !Array.isArray(input.sessions) || !Array.isArray(input.progression)) fail('Formato de backup incompatível.');
    if (input.sessions.length > MAX_RECORDS || input.progression.length > MAX_RECORDS || Object.keys(input.settings).length > validExercises.size) fail('O backup ultrapassa o limite de registros.');
    const clean = {schemaVersion: 1, updatedAt: timestamp(input.updatedAt), settings: {}, sessions: [], progression: []};
    for (const [id, value] of Object.entries(input.settings)) {
      exerciseId(id);
      clean.settings[id] = {...series(value), updatedAt: timestamp(value.updatedAt, true)};
    }
    const ids = new Set();
    let activeCount = 0;
    for (const item of input.sessions) {
      if (!object(item) || typeof item.id !== 'string' || !item.id || item.id.length > 100 || ids.has(item.id) || !workoutIds.has(item.workoutId) || !object(item.exercises)) fail('Treino inválido no backup.');
      ids.add(item.id);
      const startedAt = timestamp(item.startedAt);
      const endedAt = timestamp(item.endedAt, true);
      const restStartedAt = timestamp(item.restStartedAt, true);
      if (endedAt && Date.parse(endedAt) < Date.parse(startedAt)) fail('O término do treino é anterior ao início.');
      if (!endedAt && ++activeCount > 1) fail('O backup contém mais de um treino em andamento.');
      if (restStartedAt && (endedAt || Date.parse(restStartedAt) < Date.parse(startedAt))) fail('Descanso inválido no backup.');
      const exercises = {};
      const allowed = new Set((window.GYMROOK_DATA.workouts.find(workout => workout.id === item.workoutId)?.blocks || []).flatMap(block => block.exerciseIds || []));
      for (const [id, value] of Object.entries(item.exercises)) {
        exerciseId(id);
        if (!allowed.has(id)) fail('O exercício não pertence à ficha informada.');
        const normalized = series(value);
        if (!Array.isArray(value.completed) || value.completed.length !== normalized.reps.length || value.completed.some(done => typeof done !== 'boolean')) fail('Conclusão de séries inválida.');
        exercises[id] = {...normalized, completed: [...value.completed]};
      }
      clean.sessions.push({id: item.id, workoutId: item.workoutId, startedAt, endedAt, restStartedAt, exercises});
    }
    const progressionKeys = new Set();
    for (const item of input.progression) {
      if (!object(item)) fail('Progressão inválida no backup.');
      exerciseId(item.exerciseId);
      const date = day(item.date);
      const key = `${item.exerciseId}:${date}`;
      if (progressionKeys.has(key)) fail('O backup repete uma edição no mesmo dia.');
      progressionKeys.add(key);
      clean.progression.push({exerciseId: item.exerciseId, date, editedAt: timestamp(item.editedAt), ...series(item)});
    }
    return clean;
  }
  function validateBackup(json) {
    try {
      if (typeof json !== 'string' || json.length > 20 * 1024 * 1024) fail('Arquivo de backup inválido ou maior que 20 MB.');
      const payload = JSON.parse(json);
      if (!object(payload) || payload.app !== 'GymRook' || payload.formatVersion !== 1) fail('Este arquivo não é um backup compatível do GymRook.');
      return validateState(payload.state);
    } catch (error) { throw new Error(error instanceof SyntaxError ? 'O arquivo não contém um JSON válido.' : error.message); }
  }
  function readRecord(key) {
    return new Promise((resolve, reject) => {
      const transaction = database.transaction(TABLE, 'readonly');
      const request = transaction.objectStore(TABLE).get(key);
      let value;
      request.onsuccess = () => { value = request.result; };
      transaction.oncomplete = () => resolve(value);
      transaction.onabort = transaction.onerror = () => reject(transaction.error || new Error('Não foi possível ler os dados locais.'));
    });
  }
  function writeRecords(values) {
    return new Promise((resolve, reject) => {
      const transaction = database.transaction(TABLE, 'readwrite');
      const store = transaction.objectStore(TABLE);
      for (const [key, value] of Object.entries(values)) store.put(value, key);
      transaction.oncomplete = resolve;
      transaction.onabort = transaction.onerror = () => reject(transaction.error || new Error('Não foi possível salvar os dados locais.'));
    });
  }
  function changeState(change) {
    return new Promise((resolve, reject) => {
      const transaction = database.transaction(TABLE, 'readwrite');
      const store = transaction.objectStore(TABLE);
      const request = store.get('state');
      let next, result, reason;
      request.onsuccess = () => {
        try {
          next = request.result ? validateState(request.result) : blankState();
          result = change(next);
          next.updatedAt = now();
          store.put(next, 'state');
        } catch (error) { reason = error; transaction.abort(); }
      };
      transaction.oncomplete = () => { state = next; resolve(copy(result ?? next)); };
      transaction.onabort = transaction.onerror = () => reject(reason || transaction.error || new Error('Não foi possível salvar. Confira o espaço livre no aparelho.'));
    });
  }
  function envelope(snapshot) { return JSON.stringify({app: 'GymRook', formatVersion: 1, exportedAt: now(), state: snapshot}, null, 2); }
  async function permission() {
    if (!externalFile) return 'unavailable';
    try { return await externalFile.queryPermission({mode: 'readwrite'}); } catch { return 'prompt'; }
  }
  async function writeFile(handle, json) {
    const writable = await handle.createWritable();
    try { await writable.write(json); await writable.close(); }
    catch (error) { try { await writable.abort(); } catch { /* Original error is more useful. */ } throw error; }
  }
  async function syncBackupMetadata() {
    const storedBackup = await readRecord('daily-backup');
    const metadata = await readRecord('backup-meta');
    externalFile = await readRecord('external-file') || null;
    backup = {...backup, date: storedBackup?.date || null, updatedAt: storedBackup?.updatedAt || null, storage: storedBackup?.storage || null, externalConnected: Boolean(externalFile), externalPermission: await permission(), externalDate: metadata?.externalDate || null, externalUpdatedAt: metadata?.externalUpdatedAt || null};
  }
  function lease(owner, release = false) {
    return new Promise((resolve, reject) => {
      const transaction = database.transaction(TABLE, 'readwrite');
      const records = transaction.objectStore(TABLE);
      const request = records.get('backup-lease');
      let acquired = false;
      request.onsuccess = () => {
        const current = request.result;
        if (release) {
          if (current?.owner === owner) records.put(null, 'backup-lease');
        } else if (!current || current.expiresAt <= Date.now()) {
          records.put({owner, expiresAt: Date.now() + 15000}, 'backup-lease');
          acquired = true;
        }
      };
      transaction.oncomplete = () => resolve(acquired);
      transaction.onabort = transaction.onerror = () => reject(transaction.error || new Error('Não foi possível acessar o backup diário.'));
    });
  }
  async function backupLock(operation) {
    if (navigator.locks?.request) return navigator.locks.request('gymrook-daily-backup', operation);
    // Older browsers still serialize file writes across tabs using a short-lived
    // IDB lease. An interrupted tab releases it automatically after expiry.
    const owner = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    for (let attempt = 0; attempt < 100; attempt++) {
      if (await lease(owner)) {
        try { return await operation(); }
        finally { await lease(owner, true); }
      }
      await new Promise(resolve => setTimeout(resolve, 25));
    }
    throw new Error('Outro treino está atualizando o backup. Tente novamente em alguns segundos.');
  }
  async function refreshBackup(activate = false) {
    const operation = async () => {
      // Another tab may have chosen a new file or updated its metadata.
      await syncBackupMetadata();
      const existing = await readRecord('daily-backup');
      if (!activate && !existing) return;
      const snapshot = await readRecord('state');
      const json = envelope(snapshot || state);
      const date = localDate();
      const updatedAt = now();
      let storage = 'indexeddb';
      let opfsError = null;
      if (navigator.storage?.getDirectory) {
        try {
          const directory = await navigator.storage.getDirectory();
          const file = await directory.getFileHandle(BACKUP_FILE, {create: true});
          await writeFile(file, json);
          storage = 'opfs';
        } catch (error) { opfsError = error; }
      }
      // This is a separate recovery snapshot, never a growing collection of files.
      await writeRecords({'daily-backup': {date, updatedAt, json, storage}});
      backup = {...backup, date, updatedAt, storage, error: null};
      if (externalFile) {
        backup.externalPermission = await permission();
        if (backup.externalPermission === 'granted') {
          try {
            await writeFile(externalFile, json);
            backup.externalDate = date;
            backup.externalUpdatedAt = updatedAt;
          } catch {
            backup.error = 'O backup local foi salvo, mas não foi possível atualizar o arquivo vinculado.';
          }
        } else {
          backup.error = 'O backup local foi salvo. Toque em autorizar para voltar a atualizar o arquivo vinculado.';
        }
      }
      // OPFS failure is recoverable: the independently stored IDB snapshot remains available.
      if (opfsError && storage === 'indexeddb') backup.storage = 'indexeddb';
      await writeRecords({'backup-meta': {externalDate: backup.externalDate, externalUpdatedAt: backup.externalUpdatedAt}});
    };
    try {
      await backupLock(operation);
    } catch {
      backup.error = 'O treino foi salvo, mas o backup diário não pôde ser atualizado. Exporte uma cópia.';
    }
    notify();
    channel?.postMessage({type: 'changed'});
  }
  function enqueue(operation, allowRecovery = false) {
    const task = queue.then(() => allowRecovery && database && initializationError ? undefined : api.ready).then(operation);
    queue = task.catch(() => {});
    return task;
  }
  function mutate(change, activateBackup = false) {
    return enqueue(async () => {
      const result = await changeState(change);
      notify();
      channel?.postMessage({type: 'changed'});
      await refreshBackup(activateBackup);
      return result;
    });
  }
  function active(snapshot = state) { return snapshot.sessions.find(session => !session.endedAt) || null; }
  function currentSeries(snapshot, id) { return copy(snapshot.settings[id] || defaults()); }
  const api = {
    ready: null,
    getState: () => copy(state),
    getActiveSession: () => copy(active()),
    getExercise: id => { exerciseId(id); return currentSeries(state, id); },
    canRestore: () => Boolean(database),
    getInitializationError: () => initializationError?.message || null,
    validateBackup: json => copy(validateBackup(json)),
    subscribe: listener => { listeners.add(listener); return () => listeners.delete(listener); },
    backupStatus: () => copy(backup),
    startSession: (workoutId, ids) => mutate(snapshot => {
      if (!workoutIds.has(workoutId)) fail('Ficha não encontrada.');
      if (active(snapshot)) fail('Já existe um treino em andamento. Finalize-o antes de iniciar outro.');
      if (snapshot.sessions.length >= MAX_RECORDS) fail('O limite de treinos foi atingido. Exporte seus dados.');
      const allowed = (window.GYMROOK_DATA.workouts.find(workout => workout.id === workoutId)?.blocks || []).flatMap(block => block.exerciseIds || []);
      const requested = ids == null ? allowed : ids;
      if (!Array.isArray(requested) || requested.some(id => !allowed.includes(id))) fail('Exercícios inválidos para esta ficha.');
      const startedAt = now();
      const session = {id: typeof crypto?.randomUUID === 'function' ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`, workoutId, startedAt, endedAt: null, restStartedAt: null, exercises: {}};
      for (const id of new Set(requested)) { exerciseId(id); const entry = currentSeries(snapshot, id); session.exercises[id] = {weights: entry.weights, reps: entry.reps, completed: entry.reps.map(() => false)}; }
      snapshot.sessions.push(session);
      return session;
    }, true),
    toggleRest: () => mutate(snapshot => {
      const session = active(snapshot);
      if (!session) fail('Inicie um treino antes de marcar descanso.');
      session.restStartedAt = session.restStartedAt ? null : now();
      return session;
    }),
    finishSession: () => mutate(snapshot => {
      const session = active(snapshot);
      if (!session) fail('Não há treino em andamento.');
      session.endedAt = new Date(Math.max(Date.now(), Date.parse(session.startedAt))).toISOString();
      session.restStartedAt = null;
      return session;
    }),
    updateExercise: (id, value) => mutate(snapshot => {
      exerciseId(id);
      const normalized = series(value);
      const current = active(snapshot)?.exercises[id] || currentSeries(snapshot, id);
      if (JSON.stringify(normalized.reps) === JSON.stringify(current.reps) && JSON.stringify(normalized.weights) === JSON.stringify(current.weights)) return current;
      const editedAt = now();
      snapshot.settings[id] = {...normalized, updatedAt: editedAt};
      const sessionExercise = active(snapshot)?.exercises[id];
      if (sessionExercise) {
        const completed = normalized.reps.map((rep, index) => sessionExercise.completed[index] === true && rep === sessionExercise.reps[index] && (normalized.weights[index] ?? null) === (sessionExercise.weights[index] ?? null));
        Object.assign(sessionExercise, normalized, {completed});
      }
      const date = localDate();
      const index = snapshot.progression.findIndex(item => item.exerciseId === id && item.date === date);
      const point = {exerciseId: id, date, editedAt, ...normalized};
      if (index >= 0) snapshot.progression[index] = point;
      else {
        if (snapshot.progression.length >= MAX_RECORDS) fail('O limite de progressão foi atingido. Exporte seus dados.');
        snapshot.progression.push(point);
      }
      return snapshot.settings[id];
    }),
    toggleSet: (id, index) => mutate(snapshot => {
      exerciseId(id);
      const item = active(snapshot)?.exercises[id];
      if (!item) fail('Inicie a ficha deste exercício antes de marcar uma série.');
      if (!Number.isInteger(index) || index < 0 || index >= item.reps.length) fail('Série não encontrada.');
      item.completed[index] = !item.completed[index];
      return item;
    }),
    exportBackup: () => enqueue(async () => { state = (await readRecord('state')) || state; return envelope(state); }),
    getDailyBackup: () => enqueue(async () => (await readRecord('daily-backup'))?.json || null, true),
    importBackup: json => {
      let replacement;
      try { replacement = validateBackup(json); }
      catch (error) { return Promise.reject(error); }
      return enqueue(async () => {
        // Import must remain usable when an existing state record is malformed.
        // Only the validated replacement is written; invalid imports never touch it.
        const next = {...copy(replacement), updatedAt: now()};
        await writeRecords({state: next});
        state = next;
        if (initializationError) { initializationError = null; api.ready = Promise.resolve(); }
        notify();
        await refreshBackup(true);
        return copy(state);
      }, true);
    },
    connectBackupFile: () => {
      if (typeof window.showSaveFilePicker !== 'function') return Promise.reject(new Error('Este navegador não permite vincular um arquivo. Use Exportar backup para salvar em Downloads ou Arquivos.'));
      // Open synchronously in the click handler, before any awaited IndexedDB operation.
      let picker;
      try { picker = window.showSaveFilePicker({suggestedName: BACKUP_FILE, types: [{description: 'Backup GymRook', accept: {'application/json': ['.json']}}]}); }
      catch (error) { return Promise.reject(error); }
      return picker.then(handle => enqueue(async () => {
        await writeRecords({'external-file': handle});
        externalFile = handle;
        backup.externalConnected = true;
        backup.externalPermission = await permission();
        await refreshBackup(true);
        return api.backupStatus();
      }));
    },
    requestBackupPermission: () => {
      if (!externalFile?.requestPermission) return Promise.reject(new Error('Vincule um arquivo de backup primeiro.'));
      let request;
      try { request = externalFile.requestPermission({mode: 'readwrite'}); } catch (error) { return Promise.reject(error); }
      return request.then(result => enqueue(async () => {
        backup.externalPermission = result;
        if (result === 'granted') await refreshBackup(true);
        else { backup.error = 'A autorização não foi concedida. O backup diário local continua disponível.'; notify(); }
        return api.backupStatus();
      }));
    }
  };
  window.GYMROOK_STORE = api;
  api.ready = new Promise((resolve, reject) => {
    if (!window.indexedDB) { initializationError = new Error('O armazenamento local não está disponível. Abra fora do modo privado ou tente outro navegador.'); reject(initializationError); return; }
    const request = window.indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => { if (!request.result.objectStoreNames.contains(TABLE)) request.result.createObjectStore(TABLE); };
    request.onerror = () => { initializationError = request.error || new Error('Não foi possível abrir o armazenamento local.'); reject(initializationError); };
    request.onblocked = () => { initializationError = new Error('Feche outras abas do GymRook e abra novamente para atualizar os dados.'); reject(initializationError); };
    request.onsuccess = async () => {
      try {
        database = request.result;
        database.onversionchange = () => { database.close(); backup.error = 'Uma atualização dos dados está disponível. Reabra o GymRook.'; notify(); };
        // Recovery information remains available even if the main state fails validation.
        await syncBackupMetadata();
        const saved = await readRecord('state');
        state = saved ? validateState(saved) : blankState();
        // Re-read inside a write transaction so simultaneous first opens cannot
        // replace a record another tab has just created.
        if (!saved) await changeState(() => {});
        if (typeof BroadcastChannel === 'function') {
          channel = new BroadcastChannel('gymrook-personal');
          channel.onmessage = () => enqueue(async () => {
            state = validateState(await readRecord('state'));
            await syncBackupMetadata();
            notify();
          }).catch(error => { backup.error = error.message; notify(); });
        }
        window.addEventListener('focus', () => enqueue(async () => { const latest = await readRecord('state'); if (latest) state = validateState(latest); await syncBackupMetadata(); notify(); }).catch(() => {}));
        if (navigator.storage?.persist) navigator.storage.persist().catch(() => {});
        resolve();
      } catch (error) { initializationError = error; reject(error); }
    };
  });
  // The UI also awaits ready; this handler prevents an unhandled rejection before it loads.
  api.ready.catch(() => {});
})();
