/** Display the original XHTML card content without changing its hierarchy.
 * Web styling is entirely separate from the e-reader/EPUB stylesheet.
 */
function renderCard(target, xhtml, baseUrl, language) {
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

  target.lang = language || documentNode.documentElement.getAttribute('xml:lang') || 'en';
  target.classList.toggle('compact', content.classList.contains('compact'));
  // Preserve the main element: responsive layouts depend on its .quote / .compact class.
  target.replaceChildren(content);
}
