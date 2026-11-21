const card = document.querySelector('#card');
const stage = document.querySelector('#card-stage');
const previous = document.querySelector('#previous');
const next = document.querySelector('#next');
const position = document.querySelector('#position');
const message = document.querySelector('#message');

let deck = [];
let currentIndex = 0;
let currentRequest = null;

function shuffle(cards) {
  const copy = [...cards];
  // Fisher-Yates: each card appears once before the shuffled deck repeats.
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

function fitCard() {
  if (card.hidden) return;
  card.style.setProperty('--card-scale', '1');
  const availableWidth = Math.max(1, stage.clientWidth - 12);
  const availableHeight = Math.max(1, stage.clientHeight - 12);
  const naturalWidth = card.offsetWidth;
  const naturalHeight = card.offsetHeight;
  const scale = Math.min(1, availableWidth / naturalWidth, availableHeight / naturalHeight);
  card.style.setProperty('--card-scale', scale.toFixed(4));
}

async function showCard(index) {
  if (!deck.length) return;
  currentRequest?.abort();
  currentIndex = (index + deck.length) % deck.length;
  const entry = deck[currentIndex];
  previous.disabled = next.disabled = false;
  position.textContent = `${String(currentIndex + 1).padStart(2, '0')} / ${String(deck.length).padStart(2, '0')}`;
  card.hidden = true;
  message.hidden = false;
  message.textContent = '正在加载卡片…';

  const request = new AbortController();
  currentRequest = request;
  try {
    const response = await fetch(entry.url, { signal: request.signal });
    if (!response.ok) throw new Error('Card unavailable');
    const content = await response.text();
    if (request.signal.aborted) return;
    renderCard(card, content, new URL(entry.url, document.baseURI), entry.language);
    card.hidden = false;
    message.hidden = true;
    card.querySelectorAll('img').forEach(img => {
      if (!img.complete) img.addEventListener('load', fitCard, { once: true });
    });
    requestAnimationFrame(fitCard);
  } catch (error) {
    if (!request.signal.aborted) message.textContent = '卡片加载失败，请切换下一张。';
  }
}

function onKeyDown(event) {
  if (event.key === 'ArrowLeft') { event.preventDefault(); showCard(currentIndex - 1); }
  if (event.key === 'ArrowRight' || event.key === ' ') {
    event.preventDefault();
    showCard(currentIndex + 1);
  }
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
    if (e.touches.length === 1) {
      touchX = e.touches[0].clientX;
      touchY = e.touches[0].clientY;
    }
  }, { passive: true });
  stage.addEventListener('touchend', e => {
    if (touchX === null || !e.changedTouches.length) return;
    const dx = e.changedTouches[0].clientX - touchX;
    const dy = e.changedTouches[0].clientY - touchY;
    if (Math.abs(dx) > 55 && Math.abs(dx) > Math.abs(dy) * 1.4) {
      showCard(currentIndex + (dx < 0 ? 1 : -1));
    }
    touchX = touchY = null;
  }, { passive: true });

  try {
    const response = await fetch('catalog.json', { cache: 'no-cache' });
    if (!response.ok) throw new Error('Catalog unavailable');
    const catalog = await response.json();
    deck = shuffle(catalog);
    if (!deck.length) throw new Error('Empty deck');
    await showCard(0);
  } catch {
    message.textContent = '无法加载卡片，请刷新页面。';
  }
}

start();
