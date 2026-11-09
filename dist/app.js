(() => {
  'use strict';
  const data = window.GYMROOK_DATA;
  const tracking = window.GYMROOK_TRACKING;
  const main = document.getElementById('main');
  const dialog = document.getElementById('info-dialog');
  if (!data || !data.workouts || !data.exercises) {
    main.innerHTML = '<div class="container"><p>Não foi possível carregar o guia. Tente abrir a página novamente.</p></div>';
    return;
  }
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const list = value => Array.isArray(value) ? value : value ? [value] : [];
  const label = value => list(value).map(esc).join(', ');
  const mediaIcon = playing => `<svg class="media-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">${playing ? '<rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>' : '<path d="M8 5v14l11-7z"/>'}</svg>`;
  const routeId = () => { try { const id = decodeURIComponent(location.hash.replace(/^#exercise\//, '')); return ['reverse-crunch', 'regular-crunch'].includes(id) ? 'lying-leg-raise' : id; } catch { return ''; } };
  const isDetail = () => location.hash.startsWith('#exercise/');
  let selected = data.workouts[0].id;
  let previousFocus = null;
  let offlineState = 'idle';
  let installPrompt = null;
  let registrationPromise = null;
  let offlineTimeout = null;
  let stopDemo = null;
  function resetOfflineTimeout() {
    clearTimeout(offlineTimeout);
    offlineTimeout = setTimeout(() => { if (offlineState === 'loading') { offlineState = 'error'; setOfflineUI(); } }, 45000);
  }
  const workouts = data.workouts;
  const exercises = data.exercises;
  const findBlock = id => {
    for (const workout of workouts) for (const block of workout.blocks || []) if ((block.exerciseIds || []).includes(id)) return {workout, block};
    return null;
  };
  const orderedIds = () => {
    const workout = workouts.find(w => w.id === selected) || workouts[0];
    return (workout.blocks || []).flatMap(b => b.exerciseIds || []).filter(id => exercises[id]);
  };
  const thumbnail = (id, exercise) => exercise.media?.poster || exercise.thumbnail || `assets/thumbnails/${id}.webp`;
  function setOfflineUI() {
    const button = document.getElementById('offline-download');
    const status = document.getElementById('offline-status');
    if (!button || !status) return;
    button.disabled = offlineState === 'loading';
    button.innerHTML = offlineState === 'loading' ? 'Preparando conteúdo <span aria-hidden="true">…</span>' : offlineState === 'ready' ? 'Disponível offline <span aria-hidden="true">✓</span>' : 'Baixar para usar offline <span aria-hidden="true">↓</span>';
    status.textContent = offlineState === 'ready' ? 'Tudo pronto para consultar sem internet neste navegador.' : offlineState === 'error' ? 'Não foi possível baixar agora. Confira a conexão e tente novamente.' : offlineState === 'unsupported' ? 'O download offline não está disponível neste navegador.' : 'Salve o guia neste navegador para consultar sem internet.';
  }
  function renderHome() {
    const workout = workouts.find(w => w.id === selected) || workouts[0];
    const blocks = workout.blocks || [];
    main.innerHTML = `<div class="container"><div class="page-top"><div class="page-title"><h1>Treinos</h1><span class="app-version">1.1</span></div><button class="button button-light" id="info-open">Guia e fontes</button></div><div class="offline-tools"><button class="button button-dark offline-button" id="offline-download"></button><p id="offline-status" class="offline-status" role="status" aria-live="polite"></p></div><section class="workout-area" aria-label="Ficha de exercícios"><div class="tabs" role="tablist" aria-label="Treinos">${workouts.map(w => `<button class="tab" role="tab" id="tab-${esc(w.id)}" aria-selected="${w.id === workout.id}" aria-controls="workout-panel" tabindex="${w.id === workout.id ? 0 : -1}" data-workout="${esc(w.id)}"><span>Treino</span><strong>${esc(w.id)}</strong></button>`).join('')}</div><div id="workout-panel" role="tabpanel" aria-labelledby="tab-${esc(workout.id)}"><div class="workout-head"><div><h2>${esc(workout.name)}</h2><p>${esc(workout.subtitle)}</p></div></div>${tracking?.workoutControls(workout) || ''}<div class="blocks">${blocks.map((block, index) => {
      const ids = (block.exerciseIds || []).filter(id => exercises[id]);
      return `<section class="exercise-group${ids.length > 1 ? ' combined-group' : ''}" aria-label="${esc(block.title)}">${ids.length > 1 ? `<div class="group-label">${ids.length > 2 ? 'Circuito' : 'Conjugado'} <span>· seguir esta sequência</span></div>` : ''}${ids.map(id => {
        const exercise = exercises[id];
        return `<div class="exercise-entry"><a class="exercise-card" href="#exercise/${encodeURIComponent(id)}" data-exercise="${esc(id)}"><div class="exercise-photo"><img src="${esc(thumbnail(id, exercise))}" width="128" height="128" loading="lazy" alt="${esc(exercise.name)}"></div><div class="exercise-card-content"><h3>${esc(exercise.name)}</h3><p class="exercise-name-en" lang="en">${esc(exercise.nameEn)}</p><div class="card-equipment"><p>${esc(exercise.equipment)}</p><p class="equipment-en" lang="en">${esc(exercise.equipmentEn)}</p></div></div></a>${tracking?.exerciseCard(id) || ''}</div>`;
      }).join('')}</section>`;
    }).join('')}</div>${data.restNote || data.safetyNote ? `<aside class="training-notes"><h2>Orientações da ficha</h2>${data.restNote ? `<p>${esc(data.restNote)}</p>` : ''}${data.safetyNote ? `<p>${esc(data.safetyNote)}</p>` : ''}</aside>` : ''}${tracking?.workoutFooter(workout) || ''}</div></section></div>`;
    tracking?.bind(main, workout);
    setOfflineUI();
    document.getElementById('offline-download').addEventListener('click', downloadOffline);
    const tabs = [...main.querySelectorAll('[role="tab"]')];
    const selectWorkout = id => {
      selected = id;
      // Keep the URL aligned with the visible tab. Otherwise a resume link to
      // the already-current hash would not navigate back from another tab.
      window.history?.replaceState(null, '', '#workout/' + selected);
      renderHome();
      tracking?.routeChanged();
      document.getElementById(`tab-${selected}`).focus();
    };
    tabs.forEach((tab, i) => {
      tab.addEventListener('click', () => selectWorkout(tab.dataset.workout));
      tab.addEventListener('keydown', event => {
        let next = i;
        if (event.key === 'ArrowRight') next = (i + 1) % tabs.length;
        else if (event.key === 'ArrowLeft') next = (i - 1 + tabs.length) % tabs.length;
        else if (event.key === 'Home') next = 0;
        else if (event.key === 'End') next = tabs.length - 1;
        else return;
        event.preventDefault(); selectWorkout(tabs[next].dataset.workout);
      });
    });
    main.querySelectorAll('[data-exercise]').forEach(a => a.addEventListener('click', () => { previousFocus = a.dataset.exercise; }));
  }
  const anatomy = exercise => typeof window.GYMROOK_ANATOMY === 'function' ? window.GYMROOK_ANATOMY(exercise) : '<p>Mapa muscular indisponível.</p>';
  function renderDetail(id) {
    const exercise = exercises[id];
    if (!exercise) { main.innerHTML = '<div class="container"><p>Exercício não encontrado.</p><a href="#">← Voltar ao treino</a></div>'; return; }
    const locationInfo = findBlock(id);
    if (locationInfo) selected = locationInfo.workout.id;
    const ids = orderedIds();
    const index = ids.indexOf(id);
    const prev = ids[index - 1], next = ids[index + 1];
    const items = (values, ordered = false) => `<${ordered ? 'ol' : 'ul'}>${list(values).map(item => `<li>${esc(item)}</li>`).join('')}</${ordered ? 'ol' : 'ul'}>`;
    const media = exercise.media;
    const navigation = position => `<nav class="detail-nav detail-nav-${position}" aria-label="Navegação entre exercícios — ${position === 'top' ? 'topo' : 'fim'}">${prev ? `<a class="nav-button" href="#exercise/${encodeURIComponent(prev)}">← Anterior</a>` : '<button class="nav-button" disabled>← Anterior</button>'}${next ? `<a class="nav-button" href="#exercise/${encodeURIComponent(next)}">Próximo →</a>` : '<button class="nav-button" disabled>Próximo →</button>'}</nav>`;
    main.innerHTML = `<div class="container"><a class="detail-back" href="#" id="detail-back"><span aria-hidden="true">←</span> Voltar ao treino ${esc(selected)}</a>${navigation('top')}<section class="detail-intro"><div><span class="eyebrow">TREINO ${esc(selected)} · GUIA DE EXERCÍCIO</span><h1>${esc(exercise.name)}</h1><p class="english">${esc(exercise.nameEn)}</p></div><span class="detail-counter">${String(index + 1).padStart(2,'0')} / ${String(ids.length).padStart(2,'0')}</span></section><div class="detail-tracking">${tracking?.exerciseCard(id) || ''}</div><div class="detail-grid"><div><div class="media-card">${media ? `<img id="demo-image" src="${esc(media.poster)}" alt="Demonstração de ${esc(exercise.name)}"><div class="media-overlay"><span class="media-label">DEMONSTRAÇÃO</span><button class="media-toggle" id="media-toggle" aria-label="Reproduzir demonstração" aria-pressed="false">${mediaIcon(false)}</button></div>` : `<img src="${esc(thumbnail(id, exercise))}" alt="Imagem de referência de ${esc(exercise.name)}"><div class="media-overlay"><span class="media-label">IMAGEM DE REFERÊNCIA</span></div>`}</div>${media ? '<p class="media-caption">Ilustração gerada por IA · piloto para revisão.</p>' : '<p class="media-caption">Animação em preparação. Consulte o passo a passo abaixo.</p>'}</div><section class="anatomy-card" aria-labelledby="muscle-title"><div class="card-top"><h2 id="muscle-title">Músculos trabalhados</h2><span>MAPA CORPORAL</span></div>${anatomy(exercise)}<div class="legend"><span>Principal</span><span>Secundário</span></div><p class="muscle-description"><strong>Principal:</strong> ${label(exercise.primary) || '—'}<br><strong>Secundário:</strong> ${label(exercise.secondary) || '—'}</p></section></div><div class="detail-content"><section class="detail-section"><span class="eyebrow">01 · PREPARAÇÃO</span><h2>Antes de começar.</h2>${items(exercise.setup)}</section><aside class="equipment-card"><span class="eyebrow">EQUIPAMENTO</span><h2>${esc(exercise.equipment)}</h2><p>${esc(exercise.equipmentEn)}</p></aside><section class="detail-section"><span class="eyebrow">02 · MOVIMENTO</span><h2>Passo a passo.</h2>${items(exercise.steps, true)}</section><section class="detail-section"><span class="eyebrow">03 · ATENÇÃO AOS DETALHES</span><h2>Pontos de atenção.</h2>${items(exercise.cues)}</section><section class="detail-section"><span class="eyebrow">04 · PARA AJUSTAR</span><h2>Evite estes erros.</h2>${items(exercise.mistakes)}</section><section class="detail-section"><span class="eyebrow">NO SEU TREINO</span><h2>Como fazer.</h2><p><strong>${esc(locationInfo?.block.prescription || '')}</strong></p>${locationInfo?.block.note ? `<p>${esc(locationInfo.block.note)}</p>` : ''}</section></div>${navigation('bottom')}</div>`;
    tracking?.bind(main);
    if (media) {
      const card = document.getElementById('demo-image').parentElement;
      const caption = main.querySelector('.media-caption');
      let generation = 0;
      const mountDemo = mode => {
        mode = mode === true ? 'legacy' : mode === false ? 'current' : mode || 'current';
        const legacy = mode === 'legacy';
        const experimental = mode === 'experimental';
        generation++;
        const ticket = generation;
        const previousVideo = card.querySelector('video');
        if (previousVideo) previousVideo.pause();
        const active = experimental ? media.experimental : legacy ? media.legacy : media;
        const isVideo = Boolean(active.video);
        const renderedScene = isVideo && active.render === '3d';
        const fps = Number(active.fps) || 12;
        const mediaCaption = active.isometric ? `Sustentação isométrica · mantenha a postura e respire · ${fps} fps.` : experimental ? `Teste de suavidade · ${fps} fps · execução não validada.` : renderedScene ? `Demonstração em 3D · ${fps} fps · piloto para revisão.` : isVideo ? `Ilustração gerada · movimento interpolado · ${fps} fps · experimental para revisão.` : 'Ilustração gerada por IA · piloto para revisão.';
        card.innerHTML = `${isVideo ? `<video id="demo-video" src="${esc(active.video)}" poster="${esc(active.poster)}" loop muted playsinline preload="none" aria-label="Demonstração de ${esc(exercise.name)}"></video>` : `<img id="demo-image" src="${esc(active.poster)}" alt="Demonstração de ${esc(exercise.name)}">`}<div class="media-overlay"><span class="media-label">${renderedScene ? 'DEMONSTRAÇÃO 3D' : 'DEMONSTRAÇÃO'}</span><button class="media-toggle" id="media-toggle" aria-label="Reproduzir demonstração" aria-pressed="false">${mediaIcon(false)}</button></div>`;
        caption.innerHTML = `<span>${esc(mediaCaption)}</span>${media.experimental?.video ? `<button type="button" class="media-version" id="media-experimental" aria-pressed="${experimental}">${experimental ? 'Voltar à versão original' : 'Testar versão suavizada'}</button>` : ''}${!experimental && media.video && media.legacy?.gif ? `<button type="button" class="media-version" id="media-version" aria-pressed="${legacy}">${legacy ? 'Ver versão atual' : 'Ver versão anterior'}</button>` : ''}<span id="media-error" class="media-error" role="status" aria-live="polite"></span>`;
        const toggle = document.getElementById('media-toggle');
        const error = document.getElementById('media-error');
        const playbackError = experimental ? 'Não foi possível reproduzir o teste. Volte à versão original ou tente novamente.' : media.legacy?.gif ? 'Não foi possível reproduzir. Tente novamente ou consulte a versão anterior.' : 'Não foi possível reproduzir. Tente novamente.';
        const video = isVideo ? document.getElementById('demo-video') : null;
        const setPlaying = playing => {
          if (ticket !== generation) return;
          toggle.setAttribute('aria-pressed', String(playing));
          toggle.setAttribute('aria-label', playing ? 'Pausar demonstração' : 'Reproduzir demonstração');
          toggle.innerHTML = mediaIcon(playing);
        };
        if (video) {
          video.muted = true;
          video.addEventListener('play', () => setPlaying(true));
          video.addEventListener('pause', () => setPlaying(false));
          video.addEventListener('error', () => {
            if (ticket !== generation) return;
            toggle.disabled = false;
            setPlaying(false);
            error.textContent = playbackError;
          });
        }
        toggle.addEventListener('click', async () => {
          if (ticket !== generation) return;
          error.textContent = '';
          if (video) {
            if (!video.paused) { video.pause(); setPlaying(false); return; }
            toggle.disabled = true;
            try {
              await video.play();
              if (ticket !== generation) { video.pause(); return; }
              setPlaying(!video.paused);
            } catch (_) {
              video.pause();
              if (ticket === generation) {
                setPlaying(false);
                error.textContent = playbackError;
              }
            } finally {
              if (ticket === generation) toggle.disabled = false;
            }
          } else {
            const playing = toggle.getAttribute('aria-pressed') === 'true';
            document.getElementById('demo-image').src = playing ? active.poster : active.gif;
            setPlaying(!playing);
          }
        });
        const variant = document.getElementById('media-version');
        if (variant) variant.addEventListener('click', () => {
          mountDemo(!legacy);
          document.getElementById('media-version').focus({preventScroll:true});
        });
        const experiment = document.getElementById('media-experimental');
        if (experiment) experiment.addEventListener('click', () => {
          mountDemo(experimental ? 'current' : 'experimental');
          document.getElementById('media-experimental').focus({preventScroll:true});
        });
      };
      stopDemo = () => {
        generation++;
        const video = card.querySelector('video');
        if (video) video.pause();
      };
      mountDemo(false);
    }
  }
  function render() {
    if (tracking?.hasPendingEdits()) {
      const target = location.hash;
      tracking.flushEdits().then(() => { if (location.hash === target) render(); }).catch(() => {});
      return;
    }
    if (stopDemo) { stopDemo(); stopDemo = null; }
    const workoutRoute = location.hash.match(/^#workout\/([ABCD])$/);
    if (workoutRoute) selected = workoutRoute[1];
    if (location.hash.startsWith('#history') || location.hash.startsWith('#progression')) {
      if (tracking?.isReady() && window.GYMROOK_HISTORY) window.GYMROOK_HISTORY.render(main, location.hash);
      else main.innerHTML = `<div class="container"><div class="page-top"><h1>Seus registros</h1></div><p>${esc(tracking?.getLoadError() || 'Carregando registros locais…')}</p>${tracking?.getLoadError() ? '<a class="button button-light" href="#backup">Ver opções de recuperação</a>' : ''}</div>`;
    } else if (location.hash.startsWith('#backup') && tracking) tracking.renderBackup(main);
    else if (isDetail()) renderDetail(routeId());
    else renderHome();
    tracking?.routeChanged();
    window.scrollTo(0, 0);
    if (!isDetail() && previousFocus) {
      const target = [...main.querySelectorAll('[data-exercise]')].find(a => a.dataset.exercise === previousFocus);
      if (target) target.focus({preventScroll:true});
      previousFocus = null;
    } else if (isDetail()) main.focus({preventScroll:true});
  }
  window.addEventListener('hashchange', render);
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && !dialog.open && isDetail()) location.hash = ''; });
  const openInfo = () => { if (typeof dialog.showModal === 'function') dialog.showModal(); else dialog.setAttribute('open', ''); };
  main.addEventListener('click', event => { if (event.target.closest('#info-open')) openInfo(); });
  document.getElementById('footer-info').addEventListener('click', openInfo);
  document.getElementById('info-close').addEventListener('click', () => dialog.close());
  document.getElementById('glossary').innerHTML = (data.glossary || []).map(item => `<dt>${esc(item.term)}</dt><dd>${esc(item.definition)}</dd>`).join('');
  document.getElementById('sources').innerHTML = (data.sources || []).map(item => `<li><a href="${esc(item.url)}" target="_blank" rel="noopener noreferrer">${esc(item.title)} ↗</a></li>`).join('');
  window.addEventListener('beforeinstallprompt', event => { event.preventDefault(); installPrompt = event; document.querySelectorAll('.install-button').forEach(b => b.hidden = false); });
  document.querySelectorAll('.install-button').forEach(button => button.addEventListener('click', async () => { if (!installPrompt) return; await installPrompt.prompt(); installPrompt = null; button.hidden = true; }));
  window.addEventListener('appinstalled', () => { installPrompt = null; document.querySelectorAll('.install-button').forEach(b => b.hidden = true); });
  async function downloadOffline() {
    if (!('serviceWorker' in navigator)) { offlineState = 'unsupported'; setOfflineUI(); return; }
    offlineState = 'loading'; setOfflineUI();
    try {
      await registrationPromise;
      const ready = await Promise.race([navigator.serviceWorker.ready, new Promise((_, reject) => setTimeout(() => reject(new Error('Service worker timeout')), 15000))]);
      const worker = ready.active || navigator.serviceWorker.controller;
      if (!worker) throw new Error('No service worker');
      resetOfflineTimeout();
      worker.postMessage({type:'DOWNLOAD_OFFLINE'});
    } catch (_) { offlineState = 'error'; setOfflineUI(); }
  }
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('message', event => {
      const message = event.data || {};
      if (message.type === 'OFFLINE_PROGRESS') { resetOfflineTimeout(); const status = document.getElementById('offline-status'); if (status) status.textContent = `Baixando conteúdo: ${message.done} de ${message.total}.`; }
      if (message.type === 'OFFLINE_READY') { clearTimeout(offlineTimeout); offlineState = 'ready'; setOfflineUI(); }
      if (message.type === 'OFFLINE_ERROR') { clearTimeout(offlineTimeout); offlineState = 'error'; setOfflineUI(); }
    });
    registrationPromise = navigator.serviceWorker.register('./sw.js');
    registrationPromise.catch(() => {});
    registrationPromise.then(() => navigator.serviceWorker.ready).then(ready => {
      if (ready.active) ready.active.postMessage({type:'CHECK_OFFLINE'});
    }).catch(() => {});
  }
  render();
  if (tracking) {
    tracking.onRefresh(() => { const scroll = window.scrollY; render(); window.scrollTo(0, scroll || 0); });
    tracking.ready.then(() => {
      if (!location.hash && tracking.isReady()) selected = window.GYMROOK_STORE.getActiveSession()?.workoutId || selected;
      render();
    });
  }
})();
