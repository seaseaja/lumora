(() => {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  // One orchestrated entrance: the page's top-level blocks, then the cards it deals out.
  // The sidebar stays still (it persists across pages via View Transitions).
  const selector = [
    '.wrap > *', '.mobile-topbar', '.feature-card', '.tarot-card', '.sign-card'
  ].join(',');
  const elements = [...new Set(document.querySelectorAll(selector))];
  if (reduceMotion || !('IntersectionObserver' in window)) return;

  elements.forEach((element, index) => {
    element.dataset.motionReveal = '';
    element.style.setProperty('--motion-order', String(index % 7));
  });
  document.documentElement.classList.add('motion-ready');

  const observer = new IntersectionObserver((entries, currentObserver) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('is-visible');
      currentObserver.unobserve(entry.target);
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -28px 0px' });

  elements.forEach((element) => observer.observe(element));
})();
