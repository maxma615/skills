/* dg-deck runtime: navigation, motion, modes.  No dependencies.
   URL flags:  #n            open slide n (1-based)
               ?static=1     no animation (final state; used for PNG/PDF)
               ?mode=scroll  showcase page (vertical scroll, animate on view)
               ?print=1      print layout (one page per slide) + static
               ?notes=1      open presenter notes panel
   Keys: ←/→/Space/PageUp/PageDown/Enter/Backspace, Home/End, 1-9, N notes, F fullscreen, S scroll mode
*/
(function(){
  const Q = new URLSearchParams(location.search), root = document.documentElement;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const mode = Q.get('print') ? 'print' : (Q.get('mode') || root.dataset.mode || 'deck');
  if (Q.get('static') === '1' || reduce || mode === 'print') root.classList.add('static');
  if (Q.get('export') === '1') root.classList.add('export');
  if (Q.get('notes') === '1') root.classList.add('notes-on');
  const deck = document.getElementById('deck');
  const slides = [...deck.querySelectorAll('.slide')];
  const page = document.getElementById('page'), progress = document.getElementById('progress');
  const notesPanel = document.getElementById('notes-panel');
  let index = -1;
  const isStatic = () => root.classList.contains('static');

  /* ---- count-up for [data-count] (text already holds the final value) ---- */
  function countUp(slide){
    slide.querySelectorAll('[data-count]').forEach(el => {
      const to = parseFloat(el.dataset.count), dec = +(el.dataset.dec || 0), fin = el.textContent;
      if (isStatic() || isNaN(to)) { el.textContent = fin; return; }
      const delay = +(el.dataset.delay || 0), dur = 1100, sep = el.dataset.sep === '1';
      const fmt = v => { let s = v.toFixed(dec); if (sep) s = s.replace(/\B(?=(\d{3})+(?!\d))/g, ','); return s; };
      el.textContent = fmt(0); const t0 = performance.now() + delay;
      const step = now => { const p = Math.min(1, Math.max(0, (now - t0) / dur)); const e = 1 - Math.pow(1 - p, 4);
        el.textContent = p >= 1 ? fin : fmt(to * e); if (p < 1) requestAnimationFrame(step); };
      requestAnimationFrame(step);
    });
  }
  function enter(slide){ slide.classList.remove('in'); void slide.offsetWidth; slide.classList.add('in'); countUp(slide); }

  /* ---- deck mode ---- */
  function fit(){ const s = Math.min(innerWidth / 1920, innerHeight / 1080); deck.style.transform = `scale(${s})`; }
  function show(i, opts = {}){
    i = Math.max(0, Math.min(slides.length - 1, i));
    if (i === index) return;
    const prev = slides[index], next = slides[i], dir = i > index ? 1 : -1;
    slides.forEach(s => s.classList.remove('leaving', 'enter', 'fadein'));
    if (prev && !isStatic()) { prev.style.setProperty('--dir', dir); prev.classList.add('leaving');
      setTimeout(() => prev.classList.remove('leaving', 'in'), 520); }
    else if (prev) prev.classList.remove('in');
    if (prev) prev.classList.remove('active');
    next.style.setProperty('--dir', dir);
    next.classList.add('active');
    if (!isStatic() && prev) { next.classList.add('enter'); if (next.dataset.layout === 'section' || next.dataset.layout === 'cover' || opts.fade) next.classList.add('fadein'); }
    enter(next); index = i;
    if (page) page.textContent = `${i + 1} / ${slides.length}`;
    if (progress) progress.style.width = `${(i + 1) / slides.length * 100}%`;
    if (notesPanel) { const n = next.querySelector('.notes'); notesPanel.innerHTML = `<b>${i + 1}</b>` + (n ? n.innerHTML : '<i>{{UI_NO_NOTES}}</i>'); }
    if (location.hash !== '#' + (i + 1)) history.replaceState(null, '', '#' + (i + 1));
    document.title = (next.dataset.title ? next.dataset.title + ' · ' : '') + root.dataset.title;
  }
  function deckMode(){
    addEventListener('resize', fit); fit();
    const go = d => show(index + d);
    document.getElementById('prev')?.addEventListener('click', e => { e.stopPropagation(); go(-1); });
    document.getElementById('next')?.addEventListener('click', e => { e.stopPropagation(); go(1); });
    document.getElementById('viewport').addEventListener('click', e => {
      if (e.target.closest('a,button,.term,input') || getSelection().toString()) return;
      go(e.clientX > innerWidth / 3 ? 1 : -1); });
    let tx = null, ty = null;
    addEventListener('touchstart', e => { tx = e.touches[0].clientX; ty = e.touches[0].clientY; }, {passive: true});
    addEventListener('touchend', e => { if (tx === null) return; const dx = e.changedTouches[0].clientX - tx, dy = e.changedTouches[0].clientY - ty;
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) go(dx < 0 ? 1 : -1); tx = null; });
    addEventListener('keydown', e => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const k = e.key;
      if (['ArrowRight', 'ArrowDown', 'PageDown', ' ', 'Enter'].includes(k)) { e.preventDefault(); go(1); }
      else if (['ArrowLeft', 'ArrowUp', 'PageUp', 'Backspace'].includes(k)) { e.preventDefault(); go(-1); }
      else if (k === 'Home') show(0); else if (k === 'End') show(slides.length - 1);
      else if (/^[1-9]$/.test(k)) show(+k - 1);
      else if (k === 'n' || k === 'N') root.classList.toggle('notes-on');
      else if (k === 'f' || k === 'F') { document.fullscreenElement ? document.exitFullscreen() : root.requestFullscreen?.(); }
      else if (k === 's' || k === 'S') { location.search = '?mode=scroll'; }
    });
    addEventListener('hashchange', () => show((parseInt(location.hash.slice(1)) || 1) - 1));
    show((parseInt(location.hash.slice(1)) || 1) - 1);
  }

  /* ---- showcase / scroll mode ---- */
  function scrollMode(){
    root.classList.add('mode-scroll');
    const frames = slides.map(s => { const f = document.createElement('div'); f.className = 'frame'; s.before(f); f.appendChild(s); s.classList.add('active'); return f; });
    const size = () => { const w = Math.min(innerWidth - 32, 1600), s = w / 1920;
      frames.forEach((f, k) => { f.style.width = w + 'px'; f.style.height = 1080 * s + 'px'; slides[k].style.transform = `scale(${s})`; }); };
    addEventListener('resize', size); size(); deck.style.paddingTop = '28px';
    if (isStatic() || !('IntersectionObserver' in window)) { slides.forEach(s => s.classList.add('in')); }
    else { const io = new IntersectionObserver(es => es.forEach(en => { if (en.isIntersecting) { enter(en.target); io.unobserve(en.target); } }), {threshold: .35});
      slides.forEach(s => io.observe(s)); }
    const onScroll = () => { const h = document.documentElement; if (progress) progress.style.width = (h.scrollTop / Math.max(1, h.scrollHeight - innerHeight) * 100) + '%'; };
    addEventListener('scroll', onScroll, {passive: true});
    const n = parseInt(location.hash.slice(1)); if (n) frames[n - 1]?.scrollIntoView();
  }

  /* ---- print mode ---- */
  function printMode(){ root.classList.add('mode-print'); slides.forEach(s => s.classList.add('active', 'in')); deck.style.transform = 'none';
    if (Q.get('autoprint') === '1') addEventListener('load', () => setTimeout(() => print(), 300)); }
  addEventListener('beforeprint', () => slides.forEach(s => s.classList.add('active')));
  addEventListener('afterprint', () => { if (mode === 'deck') slides.forEach((s, k) => s.classList.toggle('active', k === index)); });

  window.DG = { show: i => show(i), get index(){ return index; }, count: slides.length, mode };
  if (mode === 'scroll') scrollMode(); else if (mode === 'print') printMode(); else deckMode();
})();

