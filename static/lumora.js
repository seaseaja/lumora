/* Lumora interactions: constellation sky, moon phase, card tilt, ripples, tarot sparkles, count-up. */
(() => {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  /* ---------- Active navigation ---------- */
  // The link with the longest matching path wins; feature pages (tarot, matrix...) belong to Dashboard.
  const path = location.pathname;
  const links = [...document.querySelectorAll('.sidebar .side-link')];
  const match = links.filter((link) => path.startsWith(link.getAttribute('href')))
    .sort((a, b) => b.getAttribute('href').length - a.getAttribute('href').length)[0]
    || links.find((link) => link.getAttribute('href') === '/dashboard');
  match?.setAttribute('aria-current', 'page');

  /* ---------- Greeting by local time ---------- */
  const greeting = document.querySelector('[data-greeting]');
  if (greeting) {
    const h = new Date().getHours();
    greeting.textContent = h < 5 ? 'Still awake? The stars are out.' : h < 11 ? 'Good morning' : h < 15 ? 'Good afternoon' : h < 19 ? 'Good evening' : 'Good night, stargazer';
  }

  /* ---------- Moon phase for today (synodic month from a known new moon) ---------- */
  const moon = document.querySelector('[data-moon]');
  if (moon) {
    const synodic = 29.530588853;
    const knownNew = Date.UTC(2000, 0, 6, 18, 14);
    const age = (((Date.now() - knownNew) / 86400000) % synodic + synodic) % synodic;
    const p = age / synodic;                       // 0 = new, .5 = full
    const lit = (1 - Math.cos(2 * Math.PI * p)) / 2; // illuminated fraction
    const names = ['New moon', 'Waxing crescent', 'First quarter', 'Waxing gibbous', 'Full moon', 'Waning gibbous', 'Last quarter', 'Waning crescent'];
    const name = names[Math.floor((p * 8) + 0.5) % 8];
    const r = 44, cx = 56, cy = 56;
    const rx = Math.abs(Math.cos(2 * Math.PI * p)) * r;
    const waxing = p < 0.5, crescent = lit < 0.5;
    const outer = waxing ? 1 : 0;
    const inner = waxing ? (crescent ? 0 : 1) : (crescent ? 1 : 0);
    const litPath = `M${cx} ${cy - r} A${r} ${r} 0 0 ${outer} ${cx} ${cy + r} A${rx.toFixed(2)} ${r} 0 0 ${inner} ${cx} ${cy - r}Z`;
    moon.innerHTML = `
      <svg viewBox="0 0 112 112" role="img" aria-label="${name}, ${Math.round(lit * 100)}% illuminated">
        <defs><radialGradient id="moonLit" cx="40%" cy="35%"><stop offset="0" stop-color="#fffaf0"/><stop offset="1" stop-color="#ffe2c4"/></radialGradient></defs>
        <circle cx="${cx}" cy="${cy}" r="${r}" fill="#3b2d73" stroke="rgba(255,255,255,.18)"/>
        <path d="${litPath}" fill="url(#moonLit)"/>
        <circle cx="44" cy="44" r="5" fill="#000" opacity=".05"/><circle cx="66" cy="70" r="7" fill="#000" opacity=".05"/><circle cx="70" cy="40" r="3" fill="#000" opacity=".05"/>
      </svg>
      <figcaption><b>${name}</b>${Math.round(lit * 100)}% lit tonight</figcaption>`;
  }

  /* ---------- Constellation canvas ---------- */
  document.querySelectorAll('[data-sky]').forEach((host) => {
    const canvas = document.createElement('canvas');
    canvas.className = 'sky-canvas';
    canvas.setAttribute('aria-hidden', 'true');
    host.prepend(canvas);
    const ctx = canvas.getContext('2d');
    const light = host.dataset.sky === 'light';
    const starColor = light ? '109, 76, 229' : '255, 247, 230';
    let stars = [], w = 0, h = 0, pointer = null, running = false, visible = true;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = host.clientWidth; h = host.clientHeight;
      canvas.width = w * dpr; canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const count = Math.round(Math.min(140, (w * h) / (light ? 5200 : 3600)));
      stars = Array.from({ length: count }, () => ({
        x: Math.random() * w, y: Math.random() * h,
        r: Math.random() * (light ? 1.4 : 1.3) + .35,
        phase: Math.random() * Math.PI * 2,
        speed: .6 + Math.random() * 1.6,
        drift: (Math.random() - .5) * .06,
      }));
      if (!running) draw(performance.now());
    };

    const draw = (t) => {
      ctx.clearRect(0, 0, w, h);
      const near = [];
      for (const s of stars) {
        if (!reduceMotion) { s.x += s.drift; if (s.x < 0) s.x += w; if (s.x > w) s.x -= w; }
        const twinkle = reduceMotion ? .8 : .45 + .55 * (0.5 + 0.5 * Math.sin(t / 1000 * s.speed + s.phase));
        let boost = 0;
        if (pointer) {
          const d = Math.hypot(s.x - pointer.x, s.y - pointer.y);
          if (d < 130) { near.push([s, d]); boost = 1 - d / 130; }
        }
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r + boost * 1.2, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${starColor}, ${Math.min(1, twinkle * (light ? .55 : 1) + boost * .5)})`;
        ctx.fill();
      }
      // Pointer draws a constellation: link the nearest stars to each other.
      if (pointer && near.length > 1) {
        near.sort((a, b) => a[1] - b[1]);
        const pts = near.slice(0, 6).map(([s]) => s);
        ctx.lineWidth = 1;
        for (let i = 0; i < pts.length - 1; i++) {
          const a = pts[i], b = pts[i + 1];
          ctx.strokeStyle = `rgba(${starColor}, ${light ? .35 : .5})`;
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        }
      }
      if (running) requestAnimationFrame(draw);
    };

    const start = () => { if (!running && visible && !reduceMotion && !document.hidden) { running = true; requestAnimationFrame(draw); } };
    const stop = () => { running = false; };

    new ResizeObserver(resize).observe(host);
    new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; visible ? start() : stop(); }).observe(host);
    document.addEventListener('visibilitychange', () => (document.hidden ? stop() : start()));
    host.addEventListener('pointermove', (e) => {
      const rect = host.getBoundingClientRect();
      pointer = { x: e.clientX - rect.left, y: e.clientY - rect.top };
      if (reduceMotion) draw(0);
    });
    host.addEventListener('pointerleave', () => { pointer = null; if (reduceMotion) draw(0); });
    resize();
    start();
  });

  /* ---------- Feature cards tilt like a card held in the hand ---------- */
  if (finePointer && !reduceMotion) {
    document.querySelectorAll('.feature-card').forEach((card) => {
      card.addEventListener('pointermove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width, y = (e.clientY - rect.top) / rect.height;
        card.classList.add('is-tilting');
        card.style.setProperty('--mx', `${x * 100}%`);
        card.style.setProperty('--my', `${y * 100}%`);
        card.style.transform = `perspective(700px) rotateX(${(0.5 - y) * 9}deg) rotateY(${(x - 0.5) * 11}deg) translateY(-4px)`;
      });
      card.addEventListener('pointerleave', () => {
        card.classList.remove('is-tilting');
        card.style.transform = '';
      });
    });
  }

  /* ---------- Ripple from the point you pressed ---------- */
  document.addEventListener('pointerdown', (e) => {
    const btn = e.target.closest('.btn, .open-btn');
    if (!btn || reduceMotion || btn.disabled) return;
    const rect = btn.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height) * 2.2;
    const ripple = document.createElement('span');
    ripple.className = 'ripple';
    Object.assign(ripple.style, {
      width: `${size}px`, height: `${size}px`,
      left: `${e.clientX - rect.left - size / 2}px`, top: `${e.clientY - rect.top - size / 2}px`,
    });
    if (getComputedStyle(btn).position === 'static') btn.style.position = 'relative';
    btn.style.overflow = 'hidden';
    btn.appendChild(ripple);
    ripple.addEventListener('animationend', () => ripple.remove());
  });

  /* ---------- Tarot: sparkle burst when a card turns over ---------- */
  const burst = (card) => {
    if (reduceMotion) return;
    card.classList.remove('just-revealed'); void card.offsetWidth; card.classList.add('just-revealed');
    const glyphs = ['✦', '✧', '⋆', '·'];
    for (let i = 0; i < 14; i++) {
      const angle = (Math.PI * 2 * i) / 14 + Math.random() * .4;
      const dist = 70 + Math.random() * 70;
      const s = document.createElement('span');
      s.className = 'sparkle';
      s.textContent = glyphs[i % glyphs.length];
      s.style.setProperty('--dx', `${Math.cos(angle) * dist}px`);
      s.style.setProperty('--dy', `${Math.sin(angle) * dist}px`);
      s.style.setProperty('--size', `${10 + Math.random() * 12}px`);
      s.style.animationDelay = `${Math.random() * 120}ms`;
      card.appendChild(s);
      s.addEventListener('animationend', () => s.remove());
    }
  };
  document.querySelectorAll('.tarot-pick-card[data-reveal-position]').forEach((card) => {
    const wasRevealed = card.classList.contains('is-revealed');
    let seen = wasRevealed;
    new MutationObserver(() => {
      if (!seen && card.classList.contains('is-revealed')) { seen = true; burst(card); }
    }).observe(card, { attributes: true, attributeFilter: ['class'] });
  });

  /* ---------- Numbers count up the first time they appear ---------- */
  const counters = [...document.querySelectorAll('.matrix-grid article b, .stats-grid article > b, .price')]
    .filter((el) => /^\s*[\d.,]+\s*$/.test(el.textContent.replace(/^Rp\s?/, '')));
  if (counters.length && !reduceMotion && 'IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      io.unobserve(entry.target);
      const el = entry.target;
      const original = el.textContent;
      const prefix = original.match(/^\s*Rp\s?/)?.[0] || '';
      const digits = original.slice(prefix.length).trim();
      const target = parseInt(digits.replace(/[^\d]/g, ''), 10);
      if (!Number.isFinite(target) || target === 0) return;
      const pad = /^0\d/.test(digits) ? digits.length : 0;
      const t0 = performance.now(), dur = 800;
      const tick = (t) => {
        const k = Math.min(1, (t - t0) / dur), eased = 1 - Math.pow(1 - k, 3);
        const n = Math.round(target * eased);
        el.textContent = k < 1 ? prefix + (pad ? String(n).padStart(pad, '0') : n.toLocaleString('en-US')) : original;
        if (k < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }), { threshold: .4 });
    counters.forEach((el) => io.observe(el));
  }
})();
