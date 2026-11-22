const card = document.querySelector('#card');
const stage = document.querySelector('#card-stage');
const previous = document.querySelector('#previous');
const next = document.querySelector('#next');
const position = document.querySelector('#position');
const message = document.querySelector('#message');

// Small bounded window: the next four cards, plus two for going backwards.
// Cache includes decoded images and the actual DOM nodes, not just card text.
const PREFETCH_AHEAD = 4;
const PREFETCH_BEHIND = 2;
const MAX_BACKGROUND_FETCHES = 2;
const MAX_CACHED_CARDS = 10;

let deck = [];
let currentIndex = 0;
let activeRecord = null;
let displayVersion = 0;
let backgroundRunning = 0;
let prefetchQueue = [];
let wantedUrls = new Set();
const cardCache = new Map();

function shuffle(cards) {
  const copy = [...cards];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

function wrappedIndex(index) {
  return (index % deck.length + deck.length) % deck.length;
}

// Never shrink the entire card, just slightly adjust typography when needed.
function fitCard() {
  if (card.hidden) return;
  const content = card.querySelector('main');
  if (!content) return;
  card.style.setProperty('--fit', '1');
  const fits = () => content.scrollHeight <= content.clientHeight + 2 && content.scrollWidth <= content.clientWidth + 2;
  if (fits()) return;
  for (let d = .96; d >= .60; d -= .04) {
    card.style.setProperty('--fit', String(Number(d.toFixed(2))));
    if (fits()) break;
  }
}

// Prepare a REAL image node while detached from the page. Reusing that node
// when showing the card means there is no second image request or fade-in.
async function prepareImage(oldImage) {
  const image = new Image();
  for (const attr of oldImage.attributes) {
    if (attr.name !== 'loading' && attr.name !== 'decoding') {
      image.setAttribute(attr.name, attr.value);
    }
  }
  image.loading = 'eager';
  image.decoding = 'async';
  oldImage.replaceWith(image);
  let loaded = false;
  try {
    if (typeof image.decode === 'function') {
      await image.decode();
    } else if (!image.complete) {
      await new Promise((resolve, reject) => {
        image.addEventListener('load', resolve, {once: true});
        image.addEventListener('error', reject, {once: true});
      });
    }
    loaded = image.naturalWidth > 0;
  } catch {
    loaded = image.complete && image.naturalWidth > 0;
  }
  const frame = image.closest('.media-frame');
  if (frame) {
    frame.classList.remove('is-loading');
    frame.classList.add(loaded ? 'is-loaded' : 'is-error');
  }
}

function prepareCard(entry) {
  const existing = cardCache.get(entry.url);
  if (existing) {
    // Map insertion order is our least-recently-used order.
    cardCache.delete(entry.url);
    cardCache.set(entry.url, existing);
    return existing;
  }

  const record = {
    entry,
    holder: document.createElement('div'),
    ready: false,
    promise: null
  };
  cardCache.set(entry.url, record);
  record.promise = (async () => {
    const response = await fetch(entry.url);
    if (!response.ok) throw new Error('Card unavailable');
    const xhtml = await response.text();
    renderCard(record.holder, xhtml, new URL(entry.url, document.baseURI), entry.language, entry.illustration_ratio);
    await Promise.all([...record.holder.querySelectorAll('.media-frame img')].map(prepareImage));
    record.ready = true;
    return record;
  })().catch(error => {
    if (cardCache.get(entry.url) === record) cardCache.delete(entry.url);
    throw error;
  });
  return record;
}

function pruneCache() {
  // Retain the active card and its nearby cards; discard older detached DOM.
  const keep = new Set(wantedUrls);
  if (activeRecord) keep.add(activeRecord.entry.url);
  for (const [url, record] of cardCache) {
    if (record.ready && !keep.has(url) && record !== activeRecord) cardCache.delete(url);
  }
  for (const [url, record] of cardCache) {
    if (cardCache.size <= MAX_CACHED_CARDS) break;
    if (record.ready && record !== activeRecord && !keep.has(url)) cardCache.delete(url);
  }
}

function drainPrefetchQueue() {
  while (backgroundRunning < MAX_BACKGROUND_FETCHES && prefetchQueue.length) {
    const entry = prefetchQueue.shift();
    if (!wantedUrls.has(entry.url) || cardCache.has(entry.url)) continue;
    backgroundRunning++;
    prepareCard(entry).promise.catch(() => {
      // A failed background request should not interrupt reading.
    }).finally(() => {
      backgroundRunning--;
      pruneCache();
      drainPrefetchQueue();
    });
  }
}

function schedulePreloads() {
  // Prioritize the next card, then nearby forward/backward cards.
  const offsets = [1, 2, -1, 3, 4, -2];
  const entries = offsets.map(offset => deck[wrappedIndex(currentIndex + offset)]);
  wantedUrls = new Set([deck[currentIndex].url, ...entries.map(entry => entry.url)]);
  prefetchQueue = entries.filter(entry => !cardCache.has(entry.url));
  pruneCache();
  drainPrefetchQueue();
}

function activateCard(record) {
  if (activeRecord && activeRecord !== record) {
    // Return the current (already decoded) nodes to their cache record.
    activeRecord.holder.replaceChildren(...card.childNodes);
  }
  if (activeRecord !== record) {
    card.replaceChildren(...record.holder.childNodes);
  }
  activeRecord = record;
  card.classList.toggle('compact', Boolean(card.querySelector('main.compact')));
  card.lang = record.entry.language || 'en';
  card.hidden = false;
  message.hidden = true;
  // Text fitting happens before the next paint, so it cannot jump afterwards.
  fitCard();
}

async function showCard(index) {
  if (!deck.length) return;
  const version = ++displayVersion;
  currentIndex = wrappedIndex(index);
  const entry = deck[currentIndex];
  previous.disabled = next.disabled = false;
  position.textContent = `${String(currentIndex + 1).padStart(2, '0')} / ${String(deck.length).padStart(2, '0')}`;

  // Cached cards are switched synchronously — no loading screen or skeleton.
  const record = prepareCard(entry);
  schedulePreloads();
  if (record.ready) {
    activateCard(record);
    return;
  }

  // A cold request can still occur after very fast taps or a network error.
  card.hidden = true;
  message.hidden = false;
  message.textContent = '正在加载卡片…';
  try {
    await record.promise;
    if (version !== displayVersion) return;
    activateCard(record);
    schedulePreloads();
  } catch {
    if (version === displayVersion) message.textContent = '卡片加载失败，请切换下一张。';
  }
}

function onKeyDown(event) {
  if (event.key === 'ArrowLeft') { event.preventDefault(); showCard(currentIndex - 1); }
  if (event.key === 'ArrowRight' || event.key === ' ') { event.preventDefault(); showCard(currentIndex + 1); }
}

async function start() {
  previous.addEventListener('click', () => showCard(currentIndex - 1));
  next.addEventListener('click', () => showCard(currentIndex + 1));
  window.addEventListener('keydown', onKeyDown);
  window.addEventListener('resize', fitCard);
  if ('ResizeObserver' in window) new ResizeObserver(fitCard).observe(stage);

  let touchX = null;
  let touchY = null;
  stage.addEventListener('touchstart', e => {
    if (e.touches.length === 1) { touchX = e.touches[0].clientX; touchY = e.touches[0].clientY; }
  }, {passive: true});
  stage.addEventListener('touchend', e => {
    if (touchX === null || !e.changedTouches.length) return;
    const dx = e.changedTouches[0].clientX - touchX;
    const dy = e.changedTouches[0].clientY - touchY;
    if (Math.abs(dx) > 55 && Math.abs(dx) > Math.abs(dy) * 1.4) showCard(currentIndex + (dx < 0 ? 1 : -1));
    touchX = touchY = null;
  }, {passive: true});

  try {
    const response = await fetch('catalog.json', {cache: 'no-cache'});
    if (!response.ok) throw new Error('Catalog unavailable');
    deck = shuffle(await response.json());
    if (!deck.length) throw new Error('Empty deck');
    await showCard(0);
  } catch { message.textContent = '无法加载卡片，请刷新页面。'; }
}
start();
