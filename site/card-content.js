/** Display the original XHTML card content without changing its hierarchy.
 * Web styling is entirely separate from the e-reader/EPUB stylesheet.
 */
function renderCard(target, xhtml, baseUrl, language, illustrationRatio) {
  const documentNode = new DOMParser().parseFromString(xhtml, 'application/xhtml+xml');
  if (documentNode.querySelector('parsererror')) {
    throw new Error('Invalid card XHTML');
  }
  const content = documentNode.querySelector('main') || documentNode.querySelector('body');
  if (!content) throw new Error('Missing card content');

  for (const el of content.querySelectorAll('img[src], a[href]')) {
    const attr = el.localName === 'img' ? 'src' : 'href';
    const value = el.getAttribute(attr);
    if (value && !value.startsWith('#')) {
      el.setAttribute(attr, new URL(value, baseUrl).href);
    }
  }

  // Reserve a real box for each illustration before the image is decoded.
  // The box determines layout; image pixels never alter its dimensions.
  for (const img of [...content.querySelectorAll('img.illustration')]) {
    const slot = documentNode.createElementNS('http://www.w3.org/1999/xhtml', 'div');
    slot.setAttribute('class', 'media-frame is-loading');
    // The prebuilt catalog contains the cropped web image's actual aspect ratio.
    // This reserves the exact pixels before the image request finishes.
    const ratio = Number(illustrationRatio);
    if (Number.isFinite(ratio) && ratio > 0.2 && ratio < 8) {
      slot.style.aspectRatio = String(ratio);
    } else {
      slot.style.aspectRatio = content.classList.contains('quote') ? '1' : '1.65';
    }
    img.replaceWith(slot);
    slot.append(img);
    img.setAttribute('decoding', 'async');
    img.setAttribute('loading', 'eager');
  }

  target.lang = language || documentNode.documentElement.getAttribute('xml:lang') || 'en';
  target.classList.toggle('compact', content.classList.contains('compact'));
  // Preserve the main element: responsive layouts depend on its .quote / .compact class.
  const index = document.createElement('span');
  index.className = 'card-index';
  target.replaceChildren(index, content);
}
