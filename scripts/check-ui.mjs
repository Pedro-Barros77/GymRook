import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const root = new URL('../dist/', import.meta.url);
const read = name => readFile(new URL(name, root), 'utf8');
const decode = text => String(text).replace(/&(#(?:x[0-9a-f]+|\d+)|amp|lt|gt|quot|apos);/gi, (_, entity) => {
  const known = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'" };
  if (entity[0] !== '#') return known[entity.toLowerCase()];
  const hex = entity[1].toLowerCase() === 'x';
  return String.fromCodePoint(parseInt(entity.slice(hex ? 2 : 1), hex ? 16 : 10));
});
const normalized = value => String(value).replace(/\s+/g, ' ').trim();
const voidTags = new Set(['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr', 'path', 'ellipse']);

// Small in-memory DOM for exercising our rendering and bound handlers. This is not
// a browser, a layout engine or a claim about real-device behavior.
class Element {
  constructor(tag, attrs = {}, document) {
    this.tagName = tag;
    this.attributes = { ...attrs };
    this.ownerDocument = document;
    this.children = [];
    this.parentElement = null;
    this.listeners = new Map();
    this.open = false;
    this.hidden = 'hidden' in attrs;
    this.disabled = 'disabled' in attrs;
    this.paused = true;
    this.currentTime = 0;
    this.playCalls = 0;
    this.pauseCalls = 0;
    this._text = null;
  }
  get dataset() { return Object.fromEntries(Object.entries(this.attributes).filter(([key]) => key.startsWith('data-')).map(([key, value]) => [key.slice(5).replace(/-([a-z])/g, (_, char) => char.toUpperCase()), value])); }
  get textContent() { return this._text ?? this.children.map(child => typeof child === 'string' ? decode(child) : child.textContent).join(''); }
  set textContent(value) { this._text = String(value); this.children = []; }
  get innerHTML() { return this._html || ''; }
  set innerHTML(html) {
    this._text = null;
    this._html = String(html);
    this.children = parse(this._html, this.ownerDocument);
    for (const child of this.children) if (typeof child !== 'string') child.parentElement = this;
  }
  get src() { return this.getAttribute('src'); }
  set src(value) { this.setAttribute('src', value); }
  getAttribute(name) { return Object.hasOwn(this.attributes, name) ? this.attributes[name] : null; }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  matches(selector) {
    if (selector.startsWith('#')) return this.getAttribute('id') === selector.slice(1);
    if (selector.startsWith('.')) return (this.getAttribute('class') || '').split(/\s+/).includes(selector.slice(1));
    const attribute = selector.match(/^\[([^=\]]+)(?:=["']?([^"'\]]+)["']?)?\]$/);
    if (attribute) return attribute[2] === undefined ? this.getAttribute(attribute[1]) !== null : this.getAttribute(attribute[1]) === attribute[2];
    return this.tagName === selector.toLowerCase();
  }
  querySelectorAll(selector) {
    const result = [];
    for (const child of this.children) if (typeof child !== 'string') {
      if (child.matches(selector)) result.push(child);
      result.push(...child.querySelectorAll(selector));
    }
    return result;
  }
  querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
  closest(selector) { return this.matches(selector) ? this : this.parentElement?.closest(selector) || null; }
  addEventListener(type, handler) {
    if (!this.listeners.has(type)) this.listeners.set(type, []);
    this.listeners.get(type).push(handler);
  }
  dispatch(type, values = {}) {
    const event = { type, target: this, defaultPrevented: false, preventDefault() { this.defaultPrevented = true; }, ...values };
    for (let current = this; current; current = current.parentElement) for (const handler of current.listeners.get(type) || []) handler(event);
    return event;
  }
  click() {
    if (this.disabled) return;
    const event = this.dispatch('click');
    if (this.tagName === 'a' && !event.defaultPrevented && this.getAttribute('href')?.startsWith('#')) this.ownerDocument.location.hash = this.getAttribute('href');
  }
  focus() { this.ownerDocument.activeElement = this; }
  async play() {
    this.playCalls++;
    if (this.playError) throw new Error('Playback blocked');
    if (this.playDeferred) await this.playDeferred;
    this.paused = false;
    this.dispatch('play');
  }
  pause() { this.paused = true; this.pauseCalls++; this.dispatch('pause'); }
  showModal() { this.open = true; }
  close() { this.open = false; }
}

function parse(html, document) {
  const root = { children: [] }, stack = [root];
  for (const token of html.match(/<!--[\s\S]*?-->|<[^>]+>|[^<]+/g) || []) {
    if (token.startsWith('<!--') || /^<!doctype/i.test(token)) continue;
    if (token.startsWith('</')) { if (stack.length > 1) stack.pop(); continue; }
    if (token.startsWith('<')) {
      const tag = token.match(/^<([\w:-]+)/)?.[1].toLowerCase();
      if (!tag) continue;
      const attrs = {};
      const raw = token.slice(tag.length + 1, token.endsWith('/>') ? -2 : -1);
      for (const match of raw.matchAll(/([\w:-]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+)))?/g)) attrs[match[1]] = decode(match[2] ?? match[3] ?? match[4] ?? '');
      const node = new Element(tag, attrs, document);
      stack.at(-1).children.push(node);
      if (stack.at(-1) instanceof Element) node.parentElement = stack.at(-1);
      if (!voidTags.has(tag) && !token.endsWith('/>')) stack.push(node);
    } else stack.at(-1).children.push(token);
  }
  return root.children;
}

function harness(html, scripts, initialHash = '') {
  const windowEvents = new Map();
  const window = { scrollTo() {}, addEventListener(type, handler) { if (!windowEvents.has(type)) windowEvents.set(type, []); windowEvents.get(type).push(handler); } };
  let currentHash = initialHash;
  const location = {
    get hash() { return currentHash; },
    set hash(value) { currentHash = value; for (const handler of windowEvents.get('hashchange') || []) handler(); }
  };
  const document = new Element('document');
  document.ownerDocument = document;
  document.location = location;
  document.getElementById = id => document.querySelector('#' + id);
  document.innerHTML = html;
  const context = vm.createContext({ window, document, location, navigator: {}, setTimeout() { return 0; }, clearTimeout() {}, console });
  for (const [filename, source] of scripts) vm.runInContext(source, context, { filename, timeout: 3000 });
  return { document, window, location, data: window.GYMROOK_DATA, main: document.getElementById('main') };
}

function assertNavigation(ui, ids, index) {
  const navs = ui.main.querySelectorAll('nav');
  assert.equal(navs.length, 2, 'Detail must provide navigation at the top and bottom');
  const normalizedNav = [];
  for (const nav of navs) {
    const controls = nav.children.filter(child => typeof child !== 'string');
    assert.equal(controls.length, 2, 'Each navigation must have two controls');
    assert.equal(normalized(controls[0].textContent), '← Anterior', 'Previous control must not repeat an exercise name');
    assert.equal(normalized(controls[1].textContent), 'Próximo →', 'Next control must not repeat an exercise name');
    assert.equal(controls[0].disabled, index === 0, 'Previous endpoint disabled state is incorrect');
    assert.equal(controls[1].disabled, index === ids.length - 1, 'Next endpoint disabled state is incorrect');
    if (index > 0) assert.equal(controls[0].getAttribute('href'), '#exercise/' + ids[index - 1]);
    if (index < ids.length - 1) assert.equal(controls[1].getAttribute('href'), '#exercise/' + ids[index + 1]);
    normalizedNav.push(controls.map(control => [control.textContent, control.getAttribute('href'), control.disabled]));
  }
  assert.deepEqual(normalizedNav[0], normalizedNav[1], 'Top and bottom navigation disagree');
}

function assertSVG(source, id) {
  assert(/^<svg\b/.test(source) && /<\/svg>$/.test(source.trim()), `${id}: invalid SVG document root`);
  assert(source.includes('xmlns="http://www.w3.org/2000/svg"'), `${id}: SVG namespace missing`);
  const tags = [];
  for (const token of source.match(/<[^>]+>/g) || []) {
    if (token.startsWith('<!--')) continue;
    const match = token.match(/^<(\/?)([\w:-]+)\b/);
    assert(match, `${id}: malformed SVG tag`);
    if (match[1]) assert.equal(tags.pop(), match[2], `${id}: mismatched SVG element`);
    else if (!token.endsWith('/>')) tags.push(match[2]);
  }
  assert.equal(tags.length, 0, `${id}: SVG has unclosed elements`);
  assert(!/(?:NaN|Infinity|undefined)/.test(source), `${id}: invalid generated SVG value`);
}

async function assertMediaControls(ui) {
  const id = 'pec-deck';
  const exercise = ui.data.exercises[id];
  const original = exercise.media;
  const legacy = original.legacy || { gif: original.gif, poster: original.poster };
  const fixture = { video: 'test-media/motion.mp4', gif: 'test-media/motion.gif', poster: 'test-media/motion-poster.webp',
                    render: 'generated-interpolated', fps: 24, frameCount: 72, legacy };
  // Exercise generic video controls using a fixture, independently of the
  // currently selected and reviewed illustration sources.
  const settle = () => new Promise(resolve => setImmediate(resolve));
  try {
    exercise.media = fixture;
    ui.location.hash = '#exercise/' + id;
    let video = ui.main.querySelector('#demo-video');
    let toggle = ui.main.querySelector('#media-toggle');
    assert(video && video.getAttribute('src') === fixture.video, 'Motion video is not the preferred demonstration');
    for (const flag of ['loop', 'muted', 'playsinline']) assert(video.getAttribute(flag) !== null, `Video is missing ${flag}`);
    assert.equal(video.getAttribute('preload'), 'none');
    assert.equal(video.getAttribute('poster'), fixture.poster);
    assert.equal(video.getAttribute('autoplay'), null, 'Demonstration must never autoplay');
    assert.equal(video.playCalls, 0, 'Opening a detail must not start the animation');
    const caption = ui.main.querySelector('.media-caption').textContent;
    assert(caption.includes('movimento interpolado · 24 fps'), 'Experimental interpolation caption is missing');
    assert(caption.includes('experimental') && !caption.includes('3D'), 'Interpolated generated media must not claim a 3D simulation');
    toggle.click(); await settle();
    assert(!video.paused && toggle.getAttribute('aria-pressed') === 'true', 'Explicit play did not start the video');
    video.currentTime = 1.25;
    toggle.click();
    assert(video.paused && toggle.getAttribute('aria-pressed') === 'false', 'Pause did not stop the video');
    assert.equal(video.currentTime, 1.25, 'Pausing should preserve the current video frame');
    video.playError = true;
    toggle.click(); await settle();
    assert(video.paused && !toggle.disabled && toggle.getAttribute('aria-pressed') === 'false', 'Rejected play left the control in a false playing state');
    assert(ui.main.querySelector('#media-error').textContent.length > 0, 'Rejected play did not explain the failure');
    video.playError = false;
    toggle.click(); await settle();
    ui.main.querySelector('#media-version').click();
    assert(video.paused, 'Switching to the prior version did not stop the current video');
    assert(!ui.main.querySelector('video'), 'Prior-version view still contains an active video');
    assert.equal(ui.main.querySelector('#demo-image').src, legacy.poster, 'Prior version must start paused at its poster');
    toggle = ui.main.querySelector('#media-toggle');
    toggle.click();
    assert.equal(ui.main.querySelector('#demo-image').src, legacy.gif, 'Prior GIF did not start after explicit play');
    toggle.click();
    assert.equal(ui.main.querySelector('#demo-image').src, legacy.poster, 'Prior GIF did not pause at its poster');
    ui.main.querySelector('#media-version').click();
    video = ui.main.querySelector('#demo-video');
    assert(video && video.paused && video.playCalls === 0, 'Returning to the current version must start paused');
    assert.equal(ui.main.querySelector('#media-toggle').getAttribute('aria-pressed'), 'false');

    // A delayed play promise must not restart a detached video after a version
    // switch, which otherwise leaks playback even with a muted element.
    let release;
    video.playDeferred = new Promise(resolve => { release = resolve; });
    ui.main.querySelector('#media-toggle').click();
    ui.main.querySelector('#media-version').click();
    release(); await settle();
    assert(video.paused, 'A stale play promise restarted the detached video');
    ui.main.querySelector('#media-version').click();
    video = ui.main.querySelector('#demo-video');
    ui.main.querySelector('#media-toggle').click(); await settle();
    ui.location.hash = '#exercise/push-up';
    assert(video.paused, 'Navigation did not stop the previous demonstration');

    exercise.media = legacy;
    ui.location.hash = '#exercise/' + id;
    assert(!ui.main.querySelector('video') && !ui.main.querySelector('#media-version'), 'Standalone generated GIF must not expose video/comparison controls');
    ui.main.querySelector('#media-toggle').click();
    assert.equal(ui.main.querySelector('#demo-image').src, legacy.gif, 'Restored 2D data must remain playable');
  } finally {
    exercise.media = original;
    ui.location.hash = '';
  }
}

async function assertExperimentalControls(ui) {
  const id = 'reverse-cable-curl';
  const exercise = ui.data.exercises[id];
  const original = exercise.media;
  const base = { gif: original.gif, poster: original.poster, render: 'generated', frameCount: 16 };
  const experimental = { video: 'test-media/experimental.mp4', gif: 'test-media/experimental.gif', poster: 'test-media/experimental-poster.webp', render: 'generated-interpolated', fps: 24, frameCount: 72 };
  const settle = () => new Promise(resolve => setImmediate(resolve));
  try {
    exercise.media = { ...base, experimental };
    ui.location.hash = '';
    const card = ui.main.querySelectorAll('[data-exercise]').find(item => item.dataset.exercise === id);
    assert.equal(card.querySelector('img').getAttribute('src'), base.poster, 'An optional experiment must not replace the card poster');
    ui.location.hash = '#exercise/' + id;
    assert(!ui.main.querySelector('video'), 'An experiment must not become the default demonstration');
    assert.equal(ui.main.querySelector('#demo-image').src, base.poster, 'Original GIF must begin paused at its own poster');
    const option = ui.main.querySelector('#media-experimental');
    assert.equal(option.textContent, 'Testar versão suavizada');
    assert.equal(option.getAttribute('aria-pressed'), 'false');
    ui.main.querySelector('#media-toggle').click();
    assert.equal(ui.main.querySelector('#demo-image').src, base.gif, 'Original GIF must remain playable before opt-in');
    option.click();
    let video = ui.main.querySelector('#demo-video');
    assert(video && video.paused && video.playCalls === 0, 'Selecting an experiment must not autoplay');
    assert.equal(video.getAttribute('src'), experimental.video);
    assert.equal(ui.main.querySelector('#media-experimental').textContent, 'Voltar à versão original');
    assert(ui.main.querySelector('.media-caption').textContent.includes('Teste de suavidade · 24 fps · execução não validada'), 'Experiment must identify its purpose and validation limit');
    ui.main.querySelector('#media-toggle').click(); await settle();
    assert(!video.paused, 'Opted-in experiment did not play after an explicit action');
    ui.main.querySelector('#media-toggle').click();
    assert(video.paused, 'Experiment did not pause');
    ui.main.querySelector('#media-toggle').click(); await settle();
    ui.main.querySelector('#media-experimental').click();
    assert(video.paused, 'Returning to the original must stop the experiment');
    assert(!ui.main.querySelector('video'));
    assert.equal(ui.main.querySelector('#demo-image').src, base.poster, 'Returning to the original must begin paused');

    ui.main.querySelector('#media-experimental').click();
    video = ui.main.querySelector('#demo-video');
    let release;
    video.playDeferred = new Promise(resolve => { release = resolve; });
    ui.main.querySelector('#media-toggle').click();
    ui.main.querySelector('#media-experimental').click();
    release(); await settle();
    assert(video.paused, 'Delayed play restarted an opted-out experiment');
    ui.main.querySelector('#media-experimental').click();
    video = ui.main.querySelector('#demo-video');
    ui.main.querySelector('#media-toggle').click(); await settle();
    ui.location.hash = '#exercise/push-up';
    assert(video.paused, 'Navigation did not stop the experimental video');
  } finally {
    exercise.media = original;
    ui.location.hash = '';
  }
}

export async function checkUI() {
  const html = await read('index.html');
  const scripts = await Promise.all(['data.js', 'anatomy.js', 'app.js'].map(async name => [name, await read(name)]));
  const scriptPaths = [...html.matchAll(/<script\b[^>]*\bsrc=["']([^"']+)["']/g)].map(match => match[1].replace(/^\.\//, ''));
  assert(scriptPaths.indexOf('anatomy.js') >= 0 && scriptPaths.indexOf('anatomy.js') < scriptPaths.indexOf('app.js'), 'Anatomy must load before the app');
  const ui = harness(html, scripts);
  assert.equal(ui.document.querySelectorAll('.brand').length, 0, 'Fictional brand header is still present');
  assert.equal(ui.document.querySelectorAll('.hero').length, 0, 'Marketing hero is still present');
  assert.equal(ui.main.querySelector('h1').textContent, 'Treinos');

  let total = 0;
  for (const workout of ui.data.workouts) {
    const tab = ui.main.querySelectorAll('[role="tab"]').find(item => item.dataset.workout === workout.id);
    assert(tab, `Missing tab ${workout.id}`);
    tab.click();
    const selected = ui.main.querySelectorAll('[role="tab"]').filter(item => item.getAttribute('aria-selected') === 'true');
    assert.equal(selected.length, 1, 'Exactly one workout must be selected');
    assert.equal(selected[0].dataset.workout, workout.id);
    const ids = workout.blocks.flatMap(block => block.exerciseIds);
    const cards = ui.main.querySelectorAll('[data-exercise]');
    assert.equal(cards.length, ids.length, `${workout.id}: wrong number of exercise cards`);
    for (const [index, card] of cards.entries()) {
      const id = ids[index], exercise = ui.data.exercises[id];
      assert.equal(card.tagName, 'a', `${id}: the full card must be a link`);
      assert.equal(card.getAttribute('href'), '#exercise/' + id);
      assert.equal(card.querySelectorAll('a').length + card.querySelectorAll('button').length, 0, `${id}: card must not contain a duplicate button/link`);
      assert(card.querySelector('img')?.getAttribute('src'), `${id}: card is missing its representative image`);
      for (const value of [exercise.name, exercise.nameEn, exercise.equipment, exercise.equipmentEn]) assert(normalized(card.textContent).includes(normalized(value)), `${id}: card is missing a bilingual label`);
      const block = workout.blocks.find(item => item.exerciseIds.includes(id));
      assert(!normalized(card.textContent).includes(normalized(block.prescription)), `${id}: prescription should be in details only`);
      if (block.note) assert(!normalized(card.textContent).includes(normalized(block.note)), `${id}: description should be in details only`);
      assert.equal(card.querySelectorAll('.prescription').length, 0, `${id}: old prescription block remains`);
      total++;
    }
    // Keyboard handling must still select and focus the next tab.
    const current = ui.main.querySelectorAll('[role="tab"]').find(item => item.dataset.workout === workout.id);
    current.dispatch('keydown', { key: 'ArrowRight' });
    const expected = ui.data.workouts[(ui.data.workouts.indexOf(workout) + 1) % ui.data.workouts.length].id;
    assert.equal(ui.document.activeElement?.dataset.workout, expected, 'Tab keyboard navigation lost focus');
  }
  assert.equal(total, 31);

  for (const workout of ui.data.workouts) {
    const ids = workout.blocks.flatMap(block => block.exerciseIds);
    for (const [index, id] of ids.entries()) {
      ui.location.hash = '#exercise/' + id;
      assertNavigation(ui, ids, index);
      const exercise = ui.data.exercises[id];
      if (exercise.media && exercise.media.render !== '3d') assert(!ui.main.querySelector('.media-caption').textContent.includes('3D'), `${id}: generated illustration is mislabeled as a 3D scene`);
      if (exercise.media && !exercise.media.legacy) assert(!ui.main.querySelector('#media-version'), `${id}: no comparison should expose a rejected/absent source`);
      assertSVG(ui.window.GYMROOK_ANATOMY(exercise), id);
      const svg = ui.main.querySelector('svg');
      assert(svg && svg.getAttribute('viewBox'), `${id}: anatomy map is missing`);
      assert(svg.querySelectorAll('[data-emphasis="primary"]').length > 0, `${id}: primary muscles are not highlighted`);
      assert(svg.querySelectorAll('[data-muscle]').length > 50, `${id}: detailed anatomical regions are missing`);
      for (const value of [exercise.name, exercise.equipment, exercise.equipmentEn]) assert(ui.main.textContent.includes(value), `${id}: detail label missing`);
    }
    // Follow an actual link to verify the bound hash-change handler, then return.
    ui.location.hash = '#exercise/' + ids[0];
    ui.main.querySelector('nav').querySelectorAll('a')[0].click();
    assert.equal(ui.location.hash, '#exercise/' + ids[1], 'Next link did not navigate');
    ui.main.querySelector('#detail-back').click();
    assert.equal(ui.main.querySelector('h1').textContent, 'Treinos');
  }

  assert(ui.document.getElementById('glossary').querySelectorAll('dt').length > 0, 'Glossary content missing');
  assert(ui.document.getElementById('sources').querySelectorAll('a').length > 0, 'Source links missing');
  ui.main.querySelector('#info-open').click();
  const dialog = ui.document.getElementById('info-dialog');
  assert(dialog.open, 'Home guide control did not open the dialog');
  ui.document.getElementById('info-close').click();
  assert(!dialog.open, 'Close guide control did not close the dialog');
  ui.document.getElementById('footer-info').click();
  assert(dialog.open, 'Footer guide control is disconnected');
  dialog.close();
  await assertMediaControls(ui);
  await assertExperimentalControls(ui);
  console.log('UI: all 31 cards/maps, paired navigation, manual playback, opt-in experiment with original GIF default, and guide controls passed (in-memory DOM; no browser/layout test).');
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  try { await checkUI(); }
  catch (error) { console.error(error.stack || error); process.exitCode = 1; }
}
