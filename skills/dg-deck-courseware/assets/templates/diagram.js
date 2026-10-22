/* dg-deck diagram runtime (NEW, not in the original 2-01 file; appended only when a deck uses layout "diagram").
   The DOM is built in its FINAL state; on slide entry the timeline resets to the initial state and plays.
   Under html.static (?static=1, ?print=1, prefers-reduced-motion) nothing plays: the final frame stays.
   Keys: R replays the diagram on the current slide. */
(function(){
  const root = document.documentElement;
  const EASE = 'cubic-bezier(.2,0,0,1)';
  const isStatic = () => root.classList.contains('static');
  const scroll = root.classList.contains('mode-scroll');
  document.querySelectorAll('.slide[data-layout=diagram]').forEach(slide => {
    const box = slide.querySelector('.dgm'); if (!box) return;
    const tl = JSON.parse(box.querySelector('script.dgm-tl').textContent);
    const svg = box.querySelector('svg.dg-svg'), cam = svg.querySelector('.cam');
    const cap = box.querySelector('.dgm-cap .t'), dots = [...box.querySelectorAll('.dgm-cap .st b')];
    const el = id => svg.querySelector(`[data-id="${id}"]`);
    const W = tl.W, H = tl.H;
    const final = {cap: cap ? cap.textContent : '', tk: {}};
    let timers = [], anims = [], camNow = [0, 0, W, H], playing = false;
    const camT = r => { const s = Math.min(W / r[2], H / r[3]); return `translate(${(W - r[2] * s) / 2 - r[0] * s}px,${(H - r[3] * s) / 2 - r[1] * s}px) scale(${s})`; };
    function camera(r, dur){ r = r === 'home' ? [0, 0, W, H] : r;
      const a = cam.animate([{transform: camT(camNow)}, {transform: camT(r)}], {duration: dur || 1100, easing: EASE, fill: 'forwards'});
      anims.push(a); camNow = r; }
    function tokenAt(id, p){ const t = el(id); const mv = t && t.querySelector('.mv'); if (mv) mv.setAttribute('transform', `translate(${p[0]},${p[1]})`); }
    function move(m){ const t = el(m.id); if (!t) return; const mv = t.querySelector('.mv');
      const pts = m.path; let L = 0; const seg = [0];
      for (let k = 1; k < pts.length; k++) { L += Math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]); seg.push(L); }
      const speed = m.speed || 0.6;                      // px per ms
      const holds = pts.map(p => p[2] || 0), total = L / speed + holds.reduce((a, b) => a + b, 0);
      const frames = []; let tcur = 0;
      for (let k = 0; k < pts.length; k++) {
        if (k) tcur += (seg[k] - seg[k - 1]) / speed;
        frames.push({transform: `translate(${pts[k][0]}px,${pts[k][1]}px)`, offset: total ? tcur / total : 0, easing: 'cubic-bezier(.4,0,.2,1)'});
        if (holds[k]) { tcur += holds[k]; frames.push({transform: `translate(${pts[k][0]}px,${pts[k][1]}px)`, offset: tcur / total, easing: 'cubic-bezier(.4,0,.2,1)'}); }
      }
      mv.removeAttribute('transform');
      frames[frames.length - 1].offset = 1;
      const a = mv.animate(frames, {duration: total, fill: 'forwards'}); anims.push(a);
      const last = pts[pts.length - 1]; a.onfinish = () => { if (!playing) return; a.cancel(); tokenAt(m.id, last); };
    }
    function setCap(text, k){ if (!cap || text == null) return;
      const a = cap.animate([{opacity: 1}, {opacity: 0}], {duration: 180, fill: 'forwards'}); anims.push(a);
      a.onfinish = () => { cap.textContent = text; a.cancel(); cap.animate([{opacity: 0, transform: 'translateY(6px)'}, {opacity: 1, transform: 'none'}], {duration: 380, easing: EASE}); };
      dots.forEach((d, j) => d.classList.toggle('on', j <= k)); }
    function step(s, k){
      (s.show || []).forEach(id => el(id)?.classList.remove('pre'));
      (s.hide || []).forEach(id => el(id)?.classList.add('pre'));
      (s.on || []).forEach(id => el(id)?.classList.add('on'));
      (s.off || []).forEach(id => el(id)?.classList.remove('on'));
      Object.entries(s.state || {}).forEach(([id, v]) => el(id)?.setAttribute('data-k', v));
      Object.entries(s.text || {}).forEach(([id, v]) => { const t = el(id)?.querySelector('text.lb, text'); if (t) t.textContent = v; });
      if ('focus' in s) { svg.querySelectorAll('.de.f').forEach(e => e.classList.remove('f'));
        if (s.focus && s.focus.length) { svg.classList.add('focusing'); s.focus.forEach(id => el(id)?.classList.add('f')); } else svg.classList.remove('focusing'); }
      if (s.camera) camera(s.camera, s.camdur);
      (s.move || []).forEach(move);
      if ('caption' in s) setCap(s.caption, s.capIndex);
    }
    function stop(){ box.classList.remove('playing'); timers.forEach(clearTimeout); timers = []; anims.forEach(a => { try { a.cancel(); } catch (e) {} }); anims = []; playing = false; }
    function toFinal(){ stop(); const I = tl.init;
      I.pre.forEach(id => el(id)?.classList.remove('pre'));
      Object.entries(tl.fin.k).forEach(([id, v]) => el(id)?.setAttribute('data-k', v));
      tl.fin.on.forEach(id => el(id)?.classList.add('on')); I.on.forEach(id => { if (!tl.fin.on.includes(id)) el(id)?.classList.remove('on'); });
      tl.fin.hidden.forEach(id => el(id)?.classList.add('pre'));
      Object.entries(tl.fin.text).forEach(([id, v]) => { const t = el(id)?.querySelector('text.lb, text'); if (t) t.textContent = v; });
      Object.entries(tl.fin.tk).forEach(([id, p]) => tokenAt(id, p));
      svg.classList.remove('focusing'); svg.querySelectorAll('.de.f').forEach(e => e.classList.remove('f'));
      cam.style.transform = ''; camNow = [0, 0, W, H];
      if (cap) cap.textContent = final.cap; dots.forEach(d => d.classList.add('on')); }
    function play(){ stop(); if (isStatic()) { toFinal(); return; } playing = true; box.classList.add('playing'); const I = tl.init;
      cam.style.transform = ''; camNow = [0, 0, W, H];
      svg.classList.remove('focusing'); svg.querySelectorAll('.de.f').forEach(e => e.classList.remove('f'));
      I.pre.forEach(id => el(id)?.classList.add('pre'));
      Object.entries(I.k).forEach(([id, v]) => el(id)?.setAttribute('data-k', v));
      tl.fin.on.forEach(id => el(id)?.classList.remove('on')); I.on.forEach(id => el(id)?.classList.add('on'));
      Object.entries(I.text).forEach(([id, v]) => { const t = el(id)?.querySelector('text.lb, text'); if (t) t.textContent = v; });
      Object.entries(I.tk).forEach(([id, p]) => tokenAt(id, p));
      if (cap) cap.textContent = I.cap; dots.forEach(d => d.classList.remove('on'));
      void svg.getBoundingClientRect();
      tl.steps.forEach((s, k) => timers.push(setTimeout(() => step(s, k), (tl.delay || 0) + s.at)));
      timers.push(setTimeout(() => { playing = false; box.classList.remove('playing'); }, (tl.delay || 0) + tl.end));
    }
    slide._dgm = {play, toFinal};
    const want = () => slide.classList.contains('in') && (scroll || root.classList.contains('mode-scroll') || slide.classList.contains('active'));
    let was = false;
    const check = () => { const w = want(); if (w && !was) play(); else if (!w && was) toFinal(); was = w; };
    new MutationObserver(check).observe(slide, {attributes: true, attributeFilter: ['class']});
    check();
  });
  addEventListener('keydown', e => { if ((e.key === 'r' || e.key === 'R') && !e.metaKey && !e.ctrlKey) {
    const s = [...document.querySelectorAll('.slide.active[data-layout=diagram]')].find(x => x.classList.contains('in'));
    if (s && s._dgm) s._dgm.play(); } });
})();
