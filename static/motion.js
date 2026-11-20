(() => {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const selector = [
    '.wrap > *', '.auth-layout', '.mobile-topbar',
    '.sidebar .brand', '.sidebar .side-label', '.sidebar .side-link',
    '.sidebar .side-logout', '.sidebar .side-user',
    '.feature-card', '.tarot-card', '.sign-card',
    '.matrix-grid > *', '.stats-grid > *', '.chat-person-card',
    '.chat-visual-card', '.chat-overview-analysis', '.chat-overview-topic-snapshot'
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
