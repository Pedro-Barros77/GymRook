(() => {
  'use strict';
  const esc = value => String(value ?? '').replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  const dayKey = value => {
    const date = value instanceof Date ? value : new Date(value);
    return Number.isNaN(date.getTime()) ? '' : `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  };
  const parseDay = value => {
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value || '');
    if (!match) return null;
    const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]), 12);
    return dayKey(date) === value ? date : null;
  };
  const longDay = value => {
    const date = parseDay(value);
    return date ? date.toLocaleDateString('pt-BR', {weekday:'long', day:'numeric', month:'long', year:'numeric'}) : 'Data indisponível';
  };
  const shortDay = value => {
    const date = parseDay(value);
    return date ? date.toLocaleDateString('pt-BR', {day:'2-digit', month:'2-digit', year:'2-digit'}) : '—';
  };
  const number = value => Number(value).toLocaleString('pt-BR', {maximumFractionDigits:2});
  const time = value => {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? '—' : date.toLocaleTimeString('pt-BR', {hour:'2-digit', minute:'2-digit'});
  };
  const duration = (start, end) => {
    const seconds = Math.max(0, Math.floor((new Date(end) - new Date(start)) / 1000));
    if (!Number.isFinite(seconds)) return '—';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor(seconds % 3600 / 60);
    const remainder = seconds % 60;
    return hours ? `${hours}h ${String(minutes).padStart(2, '0')}min` : `${minutes}min ${String(remainder).padStart(2, '0')}s`;
  };
  const completedCount = exercise => (exercise?.completed || []).filter(Boolean).length;
  const completedExercise = exercise => Array.isArray(exercise?.reps) && exercise.reps.length > 0 && completedCount(exercise) >= exercise.reps.length;
  const completedSessions = state => (state.sessions || []).filter(session => session.endedAt && dayKey(session.startedAt)).sort((a, b) => new Date(b.startedAt) - new Date(a.startedAt));

  function sessionCard(session, exercises) {
    const entries = Object.entries(session.exercises || {});
    const finished = entries.filter(([, exercise]) => completedExercise(exercise)).length;
    const doneSets = entries.reduce((sum, [, exercise]) => sum + completedCount(exercise), 0);
    const plannedSets = entries.reduce((sum, [, exercise]) => sum + (exercise.reps || []).length, 0);
    const endDay = dayKey(session.endedAt);
    const endTime = endDay !== dayKey(session.startedAt) ? `${shortDay(endDay)} às ${time(session.endedAt)}` : time(session.endedAt);
    return `<article class="history-session"><div class="history-session-head"><h3>Treino ${esc(session.workoutId)}</h3><strong>${duration(session.startedAt, session.endedAt)}</strong></div><dl class="history-session-facts"><div><dt>Início</dt><dd>${time(session.startedAt)}</dd></div><div><dt>Fim</dt><dd>${endTime}</dd></div><div><dt>Exercícios concluídos</dt><dd>${finished} de ${entries.length}</dd></div><div><dt>Séries concluídas</dt><dd>${doneSets} de ${plannedSets}</dd></div></dl><details class="history-session-details"><summary>Ver exercícios e séries</summary><ul>${entries.map(([id, exercise]) => `<li><div class="history-exercise-title"><strong>${esc(exercises[id]?.name || id)}</strong><span>${completedCount(exercise)}/${(exercise.reps || []).length} séries</span></div><ol class="history-set-list">${(exercise.reps || []).map((reps, index) => `<li><span class="history-set-state" aria-label="${exercise.completed?.[index] ? 'Concluída' : 'Não concluída'}">${exercise.completed?.[index] ? '✓' : '○'}</span><span>Série ${index + 1}: ${number(reps)} rep. · ${exercise.weights?.[index] == null ? 'carga não informada' : `${number(exercise.weights[index])} kg`}</span></li>`).join('')}</ol></li>`).join('')}</ul></details></article>`;
  }

  function renderCalendar(container, state, exercises) {
    const sessions = completedSessions(state);
    const grouped = new Map();
    for (const session of sessions) {
      const date = dayKey(session.startedAt);
      if (!grouped.has(date)) grouped.set(date, []);
      grouped.get(date).push(session);
    }
    const today = dayKey(new Date());
    let selected = grouped.has(today) ? today : sessions.length ? dayKey(sessions[0].startedAt) : today;
    let month = parseDay(selected);
    month.setDate(1);
    const draw = focus => {
      const year = month.getFullYear();
      const monthIndex = month.getMonth();
      const offset = (new Date(year, monthIndex, 1).getDay() + 6) % 7;
      const days = new Date(year, monthIndex + 1, 0).getDate();
      const monthName = month.toLocaleDateString('pt-BR', {month:'long', year:'numeric'});
      const prefix = `${year}-${String(monthIndex + 1).padStart(2, '0')}-`;
      const trainedDays = [...grouped.keys()].filter(key => key.startsWith(prefix)).length;
      const currentSessions = grouped.get(selected) || [];
      const active = (state.sessions || []).find(session => !session.endedAt && dayKey(session.startedAt) === selected);
      container.innerHTML = `<div class="container history-page"><div class="page-top"><h1>Histórico de treinos</h1></div><p class="history-description">Os dias marcados têm pelo menos um treino finalizado. Toque em um dia para consultar.</p><div class="history-layout"><section class="history-calendar" aria-labelledby="history-month"><div class="history-calendar-head"><button class="icon-button" type="button" id="history-month-prev" aria-label="Mês anterior">‹</button><h2 id="history-month" aria-live="polite">${esc(monthName)}</h2><button class="icon-button" type="button" id="history-month-next" aria-label="Próximo mês">›</button></div><div class="history-calendar-weekdays" aria-hidden="true">${['Seg','Ter','Qua','Qui','Sex','Sáb','Dom'].map(day => `<span>${day}</span>`).join('')}</div><div class="history-calendar-days">${Array.from({length:offset}, () => '<span class="history-calendar-blank" aria-hidden="true"></span>').join('')}${Array.from({length:days}, (_, index) => {
        const date = `${prefix}${String(index + 1).padStart(2, '0')}`;
        const count = (grouped.get(date) || []).length;
        return `<button type="button" class="history-calendar-day${count ? ' has-workout' : ''}${date === today ? ' is-today' : ''}" data-history-day="${date}" aria-pressed="${date === selected}" ${date === today ? 'aria-current="date"' : ''} aria-label="${esc(longDay(date))}${count ? `, ${count} treino${count > 1 ? 's' : ''} finalizado${count > 1 ? 's' : ''}` : ', sem treino finalizado'}"><span>${index + 1}</span><span class="history-calendar-mark" aria-hidden="true">${count > 1 ? count : count ? '●' : ''}</span></button>`;
      }).join('')}</div><p class="history-calendar-note"><span class="history-calendar-dot" aria-hidden="true"></span>${trainedDays} dia${trainedDays === 1 ? '' : 's'} de treino neste mês</p><button class="button button-light" type="button" id="history-today">Ir para hoje</button></section><section class="history-day-details" aria-labelledby="history-selected-day"><h2 id="history-selected-day">${esc(longDay(selected))}</h2>${active ? '<p class="history-ongoing">Há um treino em andamento neste dia. Ele aparecerá no calendário quando for finalizado.</p>' : ''}${currentSessions.length ? currentSessions.map(session => sessionCard(session, exercises)).join('') : '<div class="history-empty"><p>Nenhum treino finalizado neste dia.</p><a class="button button-light" href="#">Ir para os treinos</a></div>'}</section></div>${!sessions.length ? '<p class="history-description">Seu histórico começa quando você iniciar e finalizar o primeiro treino.</p>' : ''}</div>`;
      container.querySelector('#history-month-prev').addEventListener('click', () => changeMonth(-1));
      container.querySelector('#history-month-next').addEventListener('click', () => changeMonth(1));
      container.querySelector('#history-today').addEventListener('click', () => { selected = today; month = parseDay(today); month.setDate(1); draw('history-today'); });
      container.querySelectorAll('[data-history-day]').forEach(button => button.addEventListener('click', () => { selected = button.dataset.historyDay; draw(`[data-history-day="${selected}"]`); }));
      if (focus) {
        const target = focus.startsWith('[') ? container.querySelector(focus) : container.querySelector(`#${focus}`);
        target?.focus({preventScroll:true});
      }
    };
    const changeMonth = delta => {
      month = new Date(month.getFullYear(), month.getMonth() + delta, 1, 12);
      const prefix = `${month.getFullYear()}-${String(month.getMonth() + 1).padStart(2, '0')}-`;
      selected = today.startsWith(prefix) ? today : [...grouped.keys()].filter(key => key.startsWith(prefix)).sort().reverse()[0] || `${prefix}01`;
      draw(delta < 0 ? 'history-month-prev' : 'history-month-next');
    };
    draw();
  }

  const metricValue = (entry, metric) => {
    if (metric === 'sets') return (entry.reps || []).length;
    if (metric === 'reps') return (entry.reps || []).reduce((sum, value) => sum + Number(value || 0), 0);
    const weights = (entry.weights || []).filter(value => value != null && Number.isFinite(Number(value)));
    return weights.length ? Math.max(...weights.map(Number)) : null;
  };
  const metrics = {weight:{label:'Maior carga por série', unit:'kg'}, reps:{label:'Total de repetições configuradas', unit:'rep.'}, sets:{label:'Quantidade de séries', unit:'séries'}};
  function graph(entries, metric) {
    const points = entries.map(entry => ({date:entry.date, value:metricValue(entry, metric)})).filter(point => point.value != null);
    if (!points.length) return '<p class="history-empty">Nenhuma carga informada. Escolha repetições ou séries para ver os registros sem peso.</p>';
    const width = 660, height = 260, left = 56, right = 23, top = 24, bottom = 48;
    const plotWidth = width - left - right, plotHeight = height - top - bottom;
    const times = points.map(point => parseDay(point.date)?.getTime() || 0);
    const earliest = Math.min(...times), latest = Math.max(...times);
    const maximum = Math.max(...points.map(point => point.value), 1);
    const ceiling = Math.ceil(maximum / 4) * 4;
    const coordinate = (point, index) => ({x:earliest === latest ? left + plotWidth / 2 : left + (times[index] - earliest) / (latest - earliest) * plotWidth, y:top + plotHeight - point.value / ceiling * plotHeight});
    const coordinates = points.map(coordinate);
    const title = `${metrics[metric].label}: ${points.length} data${points.length > 1 ? 's' : ''} de edição`;
    const labels = [...new Set([0, Math.floor((points.length - 1) / 2), points.length - 1])];
    return `<svg class="history-chart" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="progression-chart-title progression-chart-description"><title id="progression-chart-title">${esc(title)}</title><desc id="progression-chart-description">${esc(`Um ponto por dia de edição, de ${shortDay(points[0].date)} a ${shortDay(points[points.length - 1].date)}. Os valores completos estão na lista abaixo.`)}</desc>${Array.from({length:5}, (_, index) => {
      const value = ceiling * index / 4;
      const y = top + plotHeight - index / 4 * plotHeight;
      return `<line class="history-chart-grid" x1="${left}" x2="${width - right}" y1="${y}" y2="${y}"/><text class="history-chart-label" x="${left - 10}" y="${y + 4}" text-anchor="end">${esc(number(value))}</text>`;
    }).join('')}<polyline class="history-chart-line" points="${coordinates.map(point => `${point.x},${point.y}`).join(' ')}"/>${coordinates.map((coordinate, index) => `<circle class="history-chart-point" cx="${coordinate.x}" cy="${coordinate.y}" r="5"><title>${esc(`${shortDay(points[index].date)}: ${number(points[index].value)} ${metrics[metric].unit}`)}</title></circle>`).join('')}${labels.map(index => `<text class="history-chart-label" x="${coordinates[index].x}" y="${height - 15}" text-anchor="${index === 0 && points.length > 1 ? 'start' : index === points.length - 1 && points.length > 1 ? 'end' : 'middle'}">${esc(shortDay(points[index].date))}</text>`).join('')}</svg>`;
  }

  function renderProgression(container, state, exercises, route) {
    const allIds = Object.keys(exercises).sort((a, b) => exercises[a].name.localeCompare(exercises[b].name, 'pt-BR'));
    let requested;
    try { requested = decodeURIComponent(route.split('/')[1] || ''); } catch { requested = ''; }
    const records = (state.progression || []).filter(entry => exercises[entry.exerciseId] && parseDay(entry.date));
    const latest = records.slice().sort((a, b) => String(b.editedAt).localeCompare(String(a.editedAt)))[0];
    let selected = exercises[requested] ? requested : latest?.exerciseId || allIds[0];
    let metric = 'weight';
    const draw = focus => {
      const daily = new Map();
      for (const entry of records.filter(entry => entry.exerciseId === selected)) {
        const previous = daily.get(entry.date);
        if (!previous || String(entry.editedAt) >= String(previous.editedAt)) daily.set(entry.date, entry);
      }
      const entries = [...daily.values()].sort((a, b) => a.date.localeCompare(b.date));
      container.innerHTML = `<div class="container history-page progression-page"><div class="page-top"><h1>Progressão</h1></div><p class="history-description">O último ajuste de cada dia vira um ponto. Marcar uma série como concluída não cria um novo registro.</p><section class="progression-controls"><label for="progression-exercise">Exercício</label><select id="progression-exercise">${allIds.map(id => `<option value="${esc(id)}"${id === selected ? ' selected' : ''}>${esc(exercises[id].name)}</option>`).join('')}</select><label for="progression-metric">Mostrar no gráfico</label><select id="progression-metric">${Object.entries(metrics).map(([key, details]) => `<option value="${key}"${key === metric ? ' selected' : ''}>${esc(details.label)} (${esc(details.unit)})</option>`).join('')}</select></section><section class="progression-plot" aria-labelledby="progression-plot-title"><div class="progression-plot-head"><h2 id="progression-plot-title">${esc(metrics[metric].label)}</h2><span>${entries.length} dia${entries.length === 1 ? '' : 's'} com ajustes</span></div>${entries.length ? graph(entries, metric) : '<div class="history-empty"><p>Ainda não há ajustes registrados para este exercício.</p><p>Edite as séries e as cargas no treino para começar.</p></div>'}<p class="history-chart-note">${metric === 'weight' ? 'A linha mostra a maior carga informada entre as séries de cada dia, em kg. Confira os valores de todas as séries abaixo.' : metric === 'reps' ? 'A linha soma as repetições configuradas em todas as séries de cada dia.' : 'A linha mostra quantas séries estavam configuradas no último ajuste de cada dia.'}</p></section>${entries.length ? `<section class="progression-records" aria-labelledby="progression-records-title"><h2 id="progression-records-title">Ajustes por dia</h2><ol class="progression-day-list">${entries.slice().reverse().map(entry => `<li class="progression-day"><div class="progression-day-heading"><h3>${esc(longDay(entry.date))}</h3><span>Último ajuste às ${time(entry.editedAt)}</span></div><div class="progression-set-chips">${(entry.reps || []).map((reps, index) => `<span><strong>Série ${index + 1}</strong> ${number(reps)} rep. · ${entry.weights?.[index] == null ? 'sem carga informada' : `${number(entry.weights[index])} kg`}</span>`).join('')}</div></li>`).join('')}</ol></section>` : ''}<a class="button button-light" href="#exercise/${encodeURIComponent(selected)}">Consultar exercício</a></div>`;
      container.querySelector('#progression-exercise').addEventListener('change', event => { selected = event.target.value; draw('progression-exercise'); });
      container.querySelector('#progression-metric').addEventListener('change', event => { metric = event.target.value; draw('progression-metric'); });
      if (focus) container.querySelector(`#${focus}`)?.focus({preventScroll:true});
    };
    draw();
  }

  window.GYMROOK_HISTORY = Object.freeze({
    render(container, route = '#history') {
      const state = window.GYMROOK_STORE.getState();
      const exercises = window.GYMROOK_DATA.exercises;
      if (route.startsWith('#progression')) renderProgression(container, state, exercises, route);
      else renderCalendar(container, state, exercises);
    }
  });
})();
