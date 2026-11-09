(() => {
  'use strict';
  const store = window.GYMROOK_STORE;
  if (!store) return;
  const data = window.GYMROOK_DATA;
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const pencil = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 5 4 4M4 20l4-1L20 7a2.8 2.8 0 0 0-4-4L4 15z"/></svg>';
  const playIcon = '<svg class="action-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M8 5v14l11-7z"/></svg>';
  const stopIcon = '<svg class="action-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect fill="currentColor" x="5" y="5" width="14" height="14" rx="1"/></svg>';
  const edits = new Map();
  const pending = new Map();
  const inFlight = new Set();
  let loaded = false;
  let loadError = '';
  let refresh = () => {};
  let lastActive = null;
  const duration = (start, now = Date.now()) => {
    const seconds = Math.max(0, Math.floor((now - new Date(start).getTime()) / 1000));
    const hours = Math.floor(seconds / 3600);
    return `${hours ? String(hours).padStart(2, '0') + ':' : ''}${String(Math.floor(seconds / 60) % 60).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
  };
  const weight = value => value == null ? 'Sem carga registrada' : `${Number(value).toLocaleString('pt-BR')} kg`;
  const active = () => loaded ? store.getActiveSession() : null;
  const config = id => active()?.exercises[id] || store.getExercise(id);
  const seriesCount = session => Object.values(session.exercises).reduce((count, ex) => count + ex.completed.filter(Boolean).length, 0);
  function announce(message, error = false) {
    const status = document.getElementById('tracking-status');
    if (!status) return;
    status.textContent = message;
    status.hidden = !message;
    status.setAttribute('data-error', String(error));
  }
  async function act(button, operation) {
    if (button?.disabled) return;
    if (button) button.disabled = true;
    try { return await operation(); }
    catch (error) { announce(error.message || 'Não foi possível salvar. Tente novamente.', true); }
    finally { if (button) button.disabled = false; }
  }
  function updateClocks() {
    const session = active();
    if (!session) return;
    const total = document.getElementById('workout-clock');
    const rest = document.getElementById('rest-clock');
    if (total) total.textContent = duration(session.startedAt);
    if (rest && session.restStartedAt) rest.textContent = duration(session.restStartedAt);
  }
  function renderBar() {
    const bar = document.getElementById('session-header');
    if (!bar) return;
    const session = active();
    bar.hidden = !session;
    if (!session) { bar.innerHTML = ''; return; }
    bar.innerHTML = `<div class="session-header-inner"><a href="#workout/${esc(session.workoutId)}" class="session-return"><span>Treino ${esc(session.workoutId)}</span><strong id="workout-clock" role="timer" aria-label="Tempo total do treino">${duration(session.startedAt)}</strong></a><button type="button" id="rest-toggle" class="rest-button${session.restStartedAt ? ' resting' : ''}" aria-pressed="${Boolean(session.restStartedAt)}" aria-label="${session.restStartedAt ? 'Encerrar e zerar descanso' : 'Iniciar descanso'}">${session.restStartedAt ? `<span id="rest-clock" role="timer" aria-label="Tempo de descanso">${duration(session.restStartedAt)}</span><span class="rest-caption">Zerar descanso</span>` : '<span class="sleep-icon" aria-hidden="true">Z<sup>z</sup><sup>z</sup></span><span class="rest-caption">Iniciar descanso</span>'}</button></div>`;
    document.getElementById('rest-toggle').addEventListener('click', event => act(event.currentTarget || document.getElementById('rest-toggle'), async () => {
      await store.toggleRest();
      renderBar();
    }));
  }
  function renderSeries(id) {
    if (!loaded) return `<p class="series-hint">${esc(loadError || 'Carregando seus registros…')}</p>`;
    const draft = edits.get(id);
    const value = draft || config(id);
    const session = active();
    const running = Boolean(session?.exercises[id]);
    const completed = running ? session.exercises[id].completed : [];
    const editButton = draft ? '<button type="button" class="button button-dark series-save" data-series-action="done">Concluir edição</button>' : `<button type="button" class="series-edit" data-series-action="edit" aria-label="Editar séries e cargas de ${esc(data.exercises[id].name)}">${pencil}<span>Editar</span></button>`;
    const previous = store.getState().sessions.filter(s => s.endedAt && s.exercises[id]).sort((a, b) => b.startedAt.localeCompare(a.startedAt))[0];
    const previousValues = previous?.exercises[id];
    const previousText = previousValues ? `<p class="previous-session">Último treino · ${new Date(previous.startedAt).toLocaleDateString('pt-BR')}: ${previousValues.reps.map((reps, i) => `${reps} rep${previousValues.weights[i] != null ? ' × ' + weight(previousValues.weights[i]) : ''}`).join(' / ')}</p>` : '';
    return `<div class="series-heading"><h4>${draft ? 'Editar séries' : 'Suas séries'}</h4>${editButton}</div>${draft ? `<div class="series-editor">${value.reps.map((reps, index) => `<div class="series-edit-row"><span class="series-number" aria-label="Série ${index + 1}">${index + 1}</span><label>Repetições<input type="number" inputmode="numeric" min="0" max="10000" step="1" data-field="reps" data-series-index="${index}" value="${esc(reps)}" aria-label="Repetições da série ${index + 1}"></label><label>Carga (kg)<input type="text" inputmode="decimal" maxlength="9" data-field="weight" data-series-index="${index}" value="${value.weights[index] == null ? '' : esc(String(value.weights[index]).replace('.', ','))}" placeholder="Opcional" aria-label="Carga em kg da série ${index + 1}"></label><button type="button" class="series-remove" data-series-action="remove" data-series-index="${index}" aria-label="Remover série ${index + 1}" ${value.reps.length <= 1 ? 'disabled' : ''}>×</button></div>`).join('')}</div><button type="button" class="button button-light series-add" data-series-action="add" ${value.reps.length >= 30 ? 'disabled' : ''}>＋ Adicionar série</button><p class="series-hint" data-save-state>As alterações são salvas automaticamente.</p>` : `<div class="series-tiles">${value.reps.map((reps, index) => `<button type="button" class="series-tile${completed[index] ? ' complete' : ''}" data-series-action="complete" data-series-index="${index}" aria-pressed="${Boolean(completed[index])}" ${!running ? 'aria-disabled="true"' : ''}><span class="series-tile-title">Série ${index + 1}<span class="series-check" aria-hidden="true">${completed[index] ? '✓' : '○'}</span></span><strong>${esc(reps)} <small>reps</small></strong><span class="series-weight">${esc(weight(value.weights[index]))}</span></button>`).join('')}</div><p class="series-hint">${running ? 'Toque em uma série para marcar ou desmarcar a conclusão.' : 'Inicie este treino para marcar as séries concluídas.'}</p>${previousText}`}<a class="series-progress-link" href="#progression/${encodeURIComponent(id)}">Ver progressão</a>`;
  }
  function exerciseCard(id) {
    return `<section class="series-card" data-series-exercise="${esc(id)}" aria-label="Séries e cargas de ${esc(data.exercises[id].name)}">${renderSeries(id)}</section>`;
  }
  function repaintSeries(card) {
    const id = card.dataset.seriesExercise;
    card.innerHTML = renderSeries(id);
    bindCard(card);
  }
  function readDraft(card) {
    const draft = edits.get(card.dataset.seriesExercise);
    if (!draft) return;
    let valid = true;
    card.querySelectorAll('input').forEach(input => {
      const index = Number(input.dataset.seriesIndex);
      const raw = input.value.trim().replace(',', '.');
      const number = raw === '' ? null : Number(raw);
      const isReps = input.dataset.field === 'reps';
      const okay = isReps ? number !== null && Number.isInteger(number) && number >= 0 && number <= 10000 : number === null || /^\d+(?:\.\d+)?$/.test(raw) && number >= 0 && number <= 10000;
      input.setAttribute('aria-invalid', String(!okay));
      if (!okay) valid = false;
      if (isReps) draft.reps[index] = number;
      else draft.weights[index] = number;
    });
    draft.valid = valid;
    return draft;
  }
  function queueSave(id) {
    const old = pending.get(id);
    if (old) clearTimeout(old.timer);
    const draft = edits.get(id);
    if (!draft?.valid) return;
    const value = {weights: [...draft.weights], reps: [...draft.reps]};
    pending.set(id, {value, timer: setTimeout(() => {
      saveDraft(id).catch(() => {});
    }, 250)});
  }
  async function saveDraft(id) {
    const item = pending.get(id);
    if (!item) return;
    clearTimeout(item.timer);
    pending.delete(id);
    const operation = store.updateExercise(id, item.value);
    inFlight.add(operation);
    try {
      await operation;
      if (!pending.has(id)) document.querySelectorAll('[data-series-exercise]').forEach(card => {
        const status = card.dataset.seriesExercise === id && card.querySelector('[data-save-state]');
        if (status && edits.get(id)?.valid) status.textContent = 'Alterações salvas neste aparelho.';
      });
    }
    catch (error) {
      // Keep the failed write available for an explicit retry instead of claiming it saved.
      if (!pending.has(id)) pending.set(id, {...item, timer: null});
      announce(`Alterações ainda não salvas: ${error.message}`, true);
      throw error;
    } finally { inFlight.delete(operation); }
  }
  async function flushEdits() {
    if ([...edits.values()].some(draft => !draft.valid)) {
      const message = 'Há campos de séries inválidos. Corrija os valores antes de continuar.';
      announce(message, true);
      throw new Error(message);
    }
    for (const id of pending.keys()) await saveDraft(id);
    await Promise.all([...inFlight]);
  }
  function discardExerciseDraft(id) {
    const item = pending.get(id);
    if (item) clearTimeout(item.timer);
    pending.delete(id);
    edits.delete(id);
    document.querySelectorAll('[data-series-exercise]').forEach(card => {
      if (card.dataset.seriesExercise === id) repaintSeries(card);
    });
  }
  function bindCard(card) {
    const id = card.dataset.seriesExercise;
    card.querySelectorAll('[data-series-action]').forEach(button => button.addEventListener('click', () => act(button, async () => {
      const action = button.dataset.seriesAction;
      if (action === 'edit') {
        const value = config(id);
        edits.set(id, {weights: [...value.weights], reps: [...value.reps], valid: true});
        repaintSeries(card);
        card.querySelector('input')?.focus({preventScroll: true});
      } else if (action === 'done') {
        const draft = readDraft(card);
        if (!draft.valid) { announce('Confira os campos destacados. Use repetições inteiras e cargas de 0 a 10.000 kg.', true); return; }
        queueSave(id);
        await saveDraft(id);
        edits.delete(id);
        repaintSeries(card);
        announce('Séries e cargas salvas neste aparelho.');
      } else if (action === 'add' || action === 'remove') {
        const draft = readDraft(card);
        if (!draft.valid) { announce('Confira os campos antes de alterar a quantidade de séries.', true); return; }
        if (action === 'add' && draft.reps.length < 30) {
          draft.reps.push(10);
          while (draft.weights.length < draft.reps.length) draft.weights.push(null);
        } else if (action === 'remove' && draft.reps.length > 1) {
          draft.reps.splice(Number(button.dataset.seriesIndex), 1);
          draft.weights.splice(Number(button.dataset.seriesIndex), 1);
        }
        queueSave(id);
        await saveDraft(id);
        repaintSeries(card);
      } else if (action === 'complete') {
        if (!active()?.exercises[id]) { announce('Inicie este treino para marcar suas séries.'); return; }
        await store.toggleSet(id, Number(button.dataset.seriesIndex));
        repaintSeries(card);
      }
    })));
    card.querySelectorAll('input').forEach(input => input.addEventListener('input', () => {
      const draft = readDraft(card);
      const state = card.querySelector('[data-save-state]');
      if (state) state.textContent = draft.valid ? 'Salvando alterações…' : 'Confira os campos destacados.';
      queueSave(id);
    }));
    card.querySelectorAll('input').forEach(input => input.addEventListener('change', () => {
      readDraft(card);
      queueSave(id);
      saveDraft(id).then(() => {
        const state = card.querySelector('[data-save-state]');
        if (state && edits.get(id)?.valid) state.textContent = 'Alterações salvas neste aparelho.';
      }).catch(() => {});
    }));
  }
  function workoutControls(workout) {
    if (!loaded) return `<div class="workout-session-actions"><button class="button button-success" disabled>${playIcon}Iniciar treino</button><p>${esc(loadError || 'Carregando registros…')}</p></div>`;
    const session = active();
    if (session) return `<div class="workout-session-actions"><p>${session.workoutId === workout.id ? 'Treino em andamento. Marque as séries conforme concluir.' : `O treino ${esc(session.workoutId)} está em andamento.`}</p>${session.workoutId !== workout.id ? `<a class="button button-dark" href="#workout/${esc(session.workoutId)}">Retomar treino ${esc(session.workoutId)}</a>` : ''}</div>`;
    return `<div class="workout-session-actions"><button type="button" class="button button-success" id="start-workout">${playIcon}Iniciar treino</button><p>O tempo e as séries ficam salvos neste aparelho.</p></div>`;
  }
  function workoutFooter(workout) {
    const session = active();
    return session?.workoutId === workout.id ? `<div class="workout-finish"><p>${seriesCount(session)} séries concluídas neste treino.</p><button type="button" class="button button-danger" id="finish-workout">${stopIcon}Finalizar treino</button></div>` : '';
  }
  function bind(main, workout) {
    main.querySelectorAll('[data-series-exercise]').forEach(bindCard);
    const start = document.getElementById('start-workout');
    if (start) start.addEventListener('click', () => act(start, async () => {
      await flushEdits();
      const ids = workout.blocks.flatMap(block => block.exerciseIds);
      await store.startSession(workout.id, ids);
      announce(`Treino ${workout.id} iniciado. Bom treino!`);
      refresh();
    }));
    const finish = document.getElementById('finish-workout');
    if (finish) finish.addEventListener('click', () => act(finish, async () => {
      await flushEdits();
      await store.finishSession();
      edits.clear();
      announce('Treino finalizado e salvo no histórico.');
      location.hash = '#history';
    }));
  }
  function routeChanged() {
    const route = location.hash;
    document.querySelectorAll('[data-app-route]').forEach(link => {
      const section = route.startsWith('#history') ? 'history' : route.startsWith('#progression') ? 'progression' : route.startsWith('#backup') ? 'backup' : 'workouts';
      if (link.dataset.appRoute === section) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
    renderBar();
  }
  function download(json, name = 'gymrook-backup.json') {
    const url = URL.createObjectURL(new Blob([json], {type: 'application/json'}));
    const link = document.createElement('a');
    link.href = url;
    link.download = name;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  }
  function backupContent() {
    return '<div class="backup-card"><h2>Exportar backup</h2><p>Salve um arquivo JSON com seus treinos, séries, cargas e progressão. Você pode guardá-lo em Downloads ou Arquivos e usá-lo para restaurar seus registros ou transferi-los para outro aparelho.</p><p>O backup é manual. Exporte uma nova cópia quando quiser atualizar o arquivo. Limpar os dados do site pode apagar seus registros neste navegador.</p><button type="button" class="button button-dark" id="backup-export">Exportar dados atuais</button></div><div class="backup-card"><h2>Restaurar um backup</h2><p>Importe um arquivo JSON exportado pelo GymRook. A restauração substitui seus registros e inclui o treino em andamento, caso exista no arquivo.</p><label class="button button-light backup-import-label" for="backup-import">Escolher arquivo de backup</label><input id="backup-import" class="backup-file-input" type="file" accept="application/json,.json"><p id="backup-import-status" role="status"></p></div><p class="backup-footnote">Seus registros ficam apenas neste aparelho e navegador. Não são enviados ao GitHub nem sincronizados com outras pessoas.</p>';
  }
  function renderBackup(main) {
    const recovery = !loaded && store.canRestore?.();
    const recoveryContent = `<p class="backup-error">${esc(loadError)}</p><div class="backup-card"><h2>Restaurar um backup</h2><p>O armazenamento está acessível, mas os registros não puderam ser lidos. Você pode restaurar um arquivo JSON exportado pelo GymRook.</p><label class="button button-light backup-import-label" for="backup-import">Escolher arquivo de backup</label><input id="backup-import" class="backup-file-input" type="file" accept="application/json,.json"><p id="backup-import-status" role="status"></p></div>`;
    main.innerHTML = `<div class="container tracking-page"><div class="page-top"><h1>Seus dados</h1></div>${loaded ? backupContent() : recovery ? recoveryContent : `<p>${esc(loadError || 'Carregando registros…')}</p>`}</div>`;
    if (!loaded && !recovery) return;
    const exportButton = document.getElementById('backup-export');
    exportButton?.addEventListener('click', () => act(exportButton, async () => {
      await flushEdits();
      download(await store.exportBackup());
      announce('Arquivo preparado. Confira o download ou salve em Arquivos.');
    }));
    document.getElementById('backup-import').addEventListener('change', async event => {
      const file = event.target.files?.[0];
      if (!file) return;
      const status = document.getElementById('backup-import-status');
      try {
        if (file.size > 20 * 1024 * 1024) throw new Error('Arquivo muito grande. Selecione um backup JSON do GymRook de até 20 MB.');
        const json = await file.text();
        const preview = JSON.parse(json);
        if (preview.app !== 'GymRook' || preview.formatVersion !== 1 || !Array.isArray(preview.state?.sessions)) throw new Error('Este arquivo não é um backup compatível do GymRook.');
        store.validateBackup?.(json);
        if (!window.confirm(`Restaurar ${file.name}? Isso substituirá todos os registros deste aparelho por ${preview.state.sessions.length} treino(s) do arquivo.`)) { event.target.value = ''; return; }
        // Cancel queued edits before replacing data, then drain already-started writes.
        // Otherwise a delayed autosave could overwrite the restored backup afterwards.
        pending.forEach(item => clearTimeout(item.timer));
        pending.clear();
        await Promise.allSettled([...inFlight]);
        pending.forEach(item => clearTimeout(item.timer));
        pending.clear();
        await store.importBackup(json);
        edits.clear();
        if (recovery) { window.location.reload(); return; }
        renderBackup(main);
        renderBar();
        announce('Backup restaurado.');
      } catch (error) {
        status.textContent = error.message || 'Não foi possível importar o arquivo.';
        announce(status.textContent, true);
      }
      event.target.value = '';
    });
  }
  const ready = store.ready.then(() => {
    loaded = true;
    lastActive = active()?.id || null;
    renderBar();
  }).catch(error => {
    loadError = 'Não foi possível abrir o armazenamento. Verifique se o navegador permite salvar dados deste site.';
    announce(`${loadError} ${error.message || ''}`, true);
  });
  store.subscribe(() => {
    if (!loaded) return;
    renderBar();
    document.querySelectorAll('[data-series-exercise]').forEach(card => {
      if (!edits.has(card.dataset.seriesExercise)) repaintSeries(card);
    });
    const session = active();
    const count = document.querySelector('.workout-finish');
    if (session && count?.querySelector('p')) count.querySelector('p').textContent = `${seriesCount(session)} séries concluídas neste treino.`;
    if ((session?.id || null) !== lastActive) { lastActive = session?.id || null; refresh(); }
  });
  setInterval(updateClocks, 1000);
  document.addEventListener('visibilitychange', () => { updateClocks(); if (document.visibilityState === 'hidden') flushEdits().catch(() => {}); });
  window.addEventListener('pagehide', () => { flushEdits().catch(() => {}); });
  window.GYMROOK_TRACKING = {ready, isReady: () => loaded, getLoadError: () => loadError, hasPendingEdits: () => pending.size > 0 || inFlight.size > 0, exerciseCard, workoutControls, workoutFooter, bind, routeChanged, renderBackup, flushEdits, discardExerciseDraft, onRefresh: callback => { refresh = callback; }};
})();
